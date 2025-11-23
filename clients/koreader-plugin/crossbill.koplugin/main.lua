local WidgetContainer = require("ui/widget/container/widgetcontainer")
local UIManager = require("ui/uimanager")
local InfoMessage = require("ui/widget/infomessage")
local MultiInputDialog = require("ui/widget/multiinputdialog")
local DocSettings = require("docsettings")
local NetworkMgr = require("ui/network/manager")
local socket = require("socket")
local http = require("socket.http")
local https = require("ssl.https")
local ltn12 = require("ltn12")
local socketutil = require("socketutil")
local JSON = require("json")
local logger = require("logger")
local _ = require("gettext")
local FileManagerBookInfo = require("apps/filemanager/filemanagerbookinfo")

local CrossbillSync = WidgetContainer:extend{
    name = "Crossbill",
    is_doc_only = true,  -- Only show when document is open
}

function CrossbillSync:init()
    -- Load settings
    self.settings = G_reader_settings:readSetting("crossbill_sync") or {
        base_url = "http://localhost:8000",
        username = "",
        password = "",
        autosync_enabled = false,
    }

    self.ui.menu:registerToMainMenu(self)

    -- Register event handlers for autosync
    self:registerEventHandlers()

    -- Track whether we enabled WiFi (so we can turn it off after sync)
    self.wifi_was_enabled_by_us = false
end

function CrossbillSync:addToMainMenu(menu_items)
    menu_items.crossbill_sync = {
        text = _("Crossbill Sync"),
        sub_item_table = {
            {
                text = _("Sync Current Book"),
                callback = function()
                    self:syncCurrentBook()
                end,
            },
            {
                text = _("Configure Server"),
                callback = function()
                    self:configureServer()
                end,
            },
            {
                text = _("Auto-sync"),
                checked_func = function()
                    return self.settings.autosync_enabled
                end,
                callback = function()
                    self.settings.autosync_enabled = not self.settings.autosync_enabled
                    G_reader_settings:saveSetting("crossbill_sync", self.settings)
                    UIManager:show(InfoMessage:new{
                        text = self.settings.autosync_enabled and
                               _("Auto-sync enabled") or
                               _("Auto-sync disabled"),
                    })
                end,
            },
        },
    }
end

function CrossbillSync:configureServer()
    local settings_dialog
    settings_dialog = MultiInputDialog:new{
        title = _("Crossbill Settings"),
        fields = {
            {
                text = self.settings.base_url or "",
                hint = _("Server URL (e.g., https://example.com)"),
            },
            {
                text = self.settings.username or "",
                hint = _("Username"),
            },
            {
                text = self.settings.password or "",
                hint = _("Password"),
                text_type = "password",
            },
        },
        buttons = {
            {
                {
                    text = _("Cancel"),
                    callback = function()
                        UIManager:close(settings_dialog)
                    end,
                },
                {
                    text = _("Save"),
                    is_enter_default = true,
                    callback = function()
                        local fields = settings_dialog:getFields()
                        -- Remove trailing slash from URL if present
                        self.settings.base_url = fields[1]:gsub("/$", "")
                        self.settings.username = fields[2]
                        self.settings.password = fields[3]
                        G_reader_settings:saveSetting("crossbill_sync", self.settings)
                        UIManager:close(settings_dialog)
                        UIManager:show(InfoMessage:new{
                            text = _("Settings saved"),
                        })
                    end,
                },
            },
        },
    }
    UIManager:show(settings_dialog)
    settings_dialog:onShowKeyboard()
end

function CrossbillSync:urlEncode(str)
    -- URL encode a string for use in form-urlencoded data
    if str then
        str = string.gsub(str, "\n", "\r\n")
        str = string.gsub(str, "([^%w _%%%-%.~])", function(c)
            return string.format("%%%02X", string.byte(c))
        end)
        str = string.gsub(str, " ", "+")
    end
    return str
end

function CrossbillSync:login()
    -- Authenticate with the server and return an access token
    -- Returns token string on success, nil on failure
    local username = self.settings.username or ""
    local password = self.settings.password or ""

    if username == "" or password == "" then
        logger.warn("Crossbill: Username or password not configured")
        return nil, "Username or password not configured"
    end

    local api_url = self.settings.base_url .. "/api/v1/auth/login"
    logger.dbg("Crossbill: Logging in to", api_url)

    -- Prepare form-urlencoded body
    local body = "username=" .. self:urlEncode(username) .. "&password=" .. self:urlEncode(password)

    local response_body = {}
    local request = {
        url = api_url,
        method = "POST",
        headers = {
            ["Content-Type"] = "application/x-www-form-urlencoded",
            ["Accept"] = "application/json",
            ["Content-Length"] = tostring(#body),
        },
        source = ltn12.source.string(body),
        sink = ltn12.sink.table(response_body),
    }

    local code
    if api_url:match("^https://") then
        code = socket.skip(1, https.request(request))
    else
        code = socket.skip(1, http.request(request))
    end
    socketutil:reset_timeout()

    if code == 200 then
        local response_text = table.concat(response_body)
        local ok, response_data = pcall(JSON.decode, response_text)
        if ok and response_data.access_token then
            logger.dbg("Crossbill: Login successful")
            return response_data.access_token
        else
            logger.err("Crossbill: Invalid login response:", response_text)
            return nil, "Invalid server response"
        end
    else
        logger.err("Crossbill: Login failed with code:", code)
        return nil, "Login failed: " .. tostring(code)
    end
end

function CrossbillSync:ensureWifiEnabled(callback)
    -- Enable WiFi if needed using NetworkMgr (the proper KOReader way)
    -- This will prompt user or auto-enable based on settings
    if NetworkMgr:willRerunWhenOnline(callback) then
        -- Network is off, NetworkMgr will call callback when online
        logger.info("crossbill: WiFi is off, prompting to enable...")
        self.wifi_was_enabled_by_us = true
        return false
    else
        -- Network is already on
        logger.info("crossbill: WiFi already enabled")
        self.wifi_was_enabled_by_us = false
        return true
    end
end

function CrossbillSync:disableWifiIfNeeded()
    -- Disable WiFi if we enabled it for the sync
    if self.wifi_was_enabled_by_us then
        logger.info("crossbill: Disabling WiFi after sync")
        NetworkMgr:turnOffWifi()
        self.wifi_was_enabled_by_us = false
    else
        logger.info("crossbill: WiFi was already on, leaving it enabled")
    end
end

function CrossbillSync:performSync(is_autosync)
    -- The actual sync logic (separated so it can be called after WiFi is enabled)
    -- is_autosync: if true, don't show result popup (silent mode)
    if not is_autosync then
        UIManager:show(InfoMessage:new{
            text = _("Syncing highlights..."),
            timeout = 2,
        })
    end

    local success, err = pcall(function()
        -- Get book metadata
        local book_props = self.ui.doc_props
        local doc_path = self.ui.document.file

        logger.dbg("Crossbill: Syncing book:", book_props.display_title or book_props.title or doc_path)

        -- Extract ISBN from identifiers if available
        -- First try from self.ui.doc_props, then fall back to reading from DocSettings
        local isbn = nil
        local doc_settings = DocSettings:open(doc_path)
        local metadata_props = doc_settings:readSetting("doc_props") or book_props

        if metadata_props.identifiers then
            -- Try to extract ISBN from identifiers string
            -- The format can vary - identifiers may be separated by newlines, spaces, or concatenated
            -- Examples: "ISBN:9780735211292\nAMAZON:..." or "ISBN:9780735211292 AMAZON:..."
            -- ISBNs are numeric with possible hyphens and X (for ISBN-10)
            -- Match ISBN: followed by digits/hyphens/X until we hit a non-ISBN character or end of string
            isbn = metadata_props.identifiers:match("ISBN:([%d%-xX]+)")
            if isbn then
                logger.dbg("Crossbill: Extracted ISBN:", isbn)
            else
                logger.dbg("Crossbill: No ISBN found in identifiers:", metadata_props.identifiers)
            end
        else
            logger.dbg("Crossbill: No identifiers field found in metadata")
        end

        local book_data = {
            title = book_props.display_title or book_props.title or self:getFilename(doc_path),
            author = book_props.authors or nil,
            isbn = isbn,
        }

        -- Get highlights from memory (ReaderAnnotation) if available,
        -- otherwise fall back to reading from DocSettings file
        local highlights = self:getHighlightsFromMemory() or self:getHighlights(doc_path)

        if not highlights or #highlights == 0 then
            UIManager:show(InfoMessage:new{
                text = _("No highlights found in this book"),
            })
            return
        end

        logger.dbg("Crossbill: Found", #highlights, "highlights")

        -- Get chapter number mapping from table of contents
        local chapter_number_map = self:getChapterNumberMap()

        -- Add chapter numbers to highlights based on their chapter names
        for _, highlight in ipairs(highlights) do
            if highlight.chapter and chapter_number_map[highlight.chapter] then
                highlight.chapter_number = chapter_number_map[highlight.chapter]
            end
        end

        -- Send to server
        self:sendToServer(book_data, highlights, is_autosync)
    end)

    if not success then
        logger.err("Crossbill: Error in syncCurrentBook:", err)
        UIManager:show(InfoMessage:new{
            text = _("Error syncing book: ") .. tostring(err),
            timeout = 5,
        })
    end

    -- Always disable WiFi after sync completes (success or failure)
    self:disableWifiIfNeeded()
end

function CrossbillSync:syncCurrentBook(is_autosync)
    -- Ensure WiFi is enabled before attempting to sync
    -- NetworkMgr will handle prompting user or auto-enabling based on settings
    -- is_autosync: if true, don't show result popup (silent mode)
    local callback = function()
        self:performSync(is_autosync)
    end

    if not self:ensureWifiEnabled(callback) then
        -- WiFi is being enabled, callback will be called when ready
        logger.info("Crossbill: Waiting for WiFi to be enabled...")
    else
        -- WiFi already on, sync immediately
        self:performSync(is_autosync)
    end
end

function CrossbillSync:getHighlightsFromMemory()
    -- Try to get highlights directly from ReaderAnnotation's memory
    -- This avoids the issue where DocSettings hasn't been flushed to disk yet
    if not self.ui.annotation then
        logger.dbg("Crossbill: ReaderAnnotation module not available")
        return nil
    end

    local annotations = self.ui.annotation.annotations
    if not annotations or #annotations == 0 then
        logger.dbg("Crossbill: No annotations in memory")
        return nil
    end

    logger.dbg("Crossbill: Found", #annotations, "annotations in memory")
    local results = {}

    for _, annotation in ipairs(annotations) do
        -- Only include highlights and notes, skip other annotation types
        if annotation.text or annotation.note then
            table.insert(results, {
                text = annotation.text or "",
                note = annotation.note or nil,
                datetime = annotation.datetime or "",
                page = annotation.pageno or annotation.page,
                chapter = annotation.chapter or nil,
            })
        end
    end

    logger.dbg("Crossbill: Converted", #results, "annotations to highlights")
    return results
end

function CrossbillSync:getHighlights(doc_path)
    local doc_settings = DocSettings:open(doc_path)
    local results = {}

    -- Try modern annotations format first
    local annotations = doc_settings:readSetting("annotations")
    if annotations then
        for _, annotation in ipairs(annotations) do
            table.insert(results, {
                text = annotation.text or "",
                note = annotation.note or nil,
                datetime = annotation.datetime or "",
                page = annotation.pageno,
                chapter = annotation.chapter or nil,
            })
        end
        return results
    end

    -- Fallback to legacy format
    local highlights = doc_settings:readSetting("highlight")
    if not highlights then
        return nil
    end

    local bookmarks = doc_settings:readSetting("bookmarks") or {}

    for page, items in pairs(highlights) do
        for _, item in ipairs(items) do
            local note = nil

            -- Find matching bookmark for note
            for _, bookmark in pairs(bookmarks) do
                if bookmark.datetime == item.datetime then
                    note = bookmark.text or nil
                    break
                end
            end

            table.insert(results, {
                text = item.text or "",
                note = note,
                datetime = item.datetime or "",
                page = item.page,
                chapter = item.chapter or nil,
            })
        end
    end

    return results
end

function CrossbillSync:getChapterNumberMap()
    -- Extract table of contents (TOC) from the document
    -- Returns a mapping from chapter name to chapter number for proper sorting
    local chapter_map = {}

    -- Get TOC from the document
    -- self.ui.toc is the TOC controller which has the toc table
    if self.ui.toc and self.ui.toc.toc then
        local toc = self.ui.toc.toc

        for i, item in ipairs(toc) do
            -- Each TOC item has a title field
            if item.title then
                chapter_map[item.title] = i
            end
        end

        logger.dbg("Crossbill: Created mapping for", #toc, "chapters from TOC")
    else
        logger.dbg("Crossbill: No TOC available for this document")
    end

    return chapter_map
end

function CrossbillSync:sendToServer(book_data, highlights, is_autosync)
    -- Wrap everything in pcall for error handling
    -- is_autosync: if true, don't show result popup (silent mode)
    local success, result = pcall(function()
        -- Login first to get auth token
        local token, login_err = self:login()
        if not token then
            if not is_autosync then
                UIManager:show(InfoMessage:new{
                    text = _("Authentication failed: ") .. (login_err or "unknown error"),
                    timeout = 5,
                })
            end
            return false, login_err
        end

        local payload = {
            book = book_data,
            highlights = highlights,
        }

        local body_json = JSON.encode(payload)

        -- Construct full API URL from host
        local api_url = self.settings.base_url .. "/api/v1/highlights/upload"
        logger.dbg("Crossbill: Sending request to", api_url)
        logger.dbg("Crossbill: Payload size:", #body_json, "bytes")

        local response_body = {}

        local request = {
            url = api_url,
            method = "POST",
            headers = {
                ["Content-Type"] = "application/json",
                ["Accept"] = "application/json",
                ["Content-Length"] = tostring(#body_json),
                ["Authorization"] = "Bearer " .. token,
            },
            source = ltn12.source.string(body_json),
            sink = ltn12.sink.table(response_body),
        }

        -- Use HTTP or HTTPS based on URL scheme
        local code
        if api_url:match("^https://") then
            logger.dbg("Crossbill: Using HTTPS")
            code = socket.skip(1, https.request(request))
        else
            logger.dbg("Crossbill: Using HTTP")
            code = socket.skip(1, http.request(request))
        end
        socketutil:reset_timeout()

        logger.dbg("Crossbill: Response code:", code)

        if code == 200 then
            local response_text = table.concat(response_body)
            logger.dbg("Crossbill: Response:", response_text)

            local ok, response_data = pcall(JSON.decode, response_text)
            if not ok then
                logger.err("Crossbill: Failed to decode JSON response:", response_text)
                return false, "Invalid server response"
            end

            -- Upload cover image if available
            if response_data.book_id then
                self:uploadCoverImage(response_data.book_id, token)
            end

            -- Only show success popup for manual syncs
            if not is_autosync then
                UIManager:show(InfoMessage:new{
                    text = string.format(
                        _("Synced successfully!\n%d new, %d duplicates"),
                        response_data.highlights_created or 0,
                        response_data.highlights_skipped or 0
                    ),
                    timeout = 3,
                })
            end
            return true
        else
            logger.err("Crossbill: Sync failed with code:", code)
            -- Only show error popup for manual syncs
            if not is_autosync then
                UIManager:show(InfoMessage:new{
                    text = _("Sync failed: ") .. tostring(code or "unknown error"),
                    timeout = 3,
                })
            end
            return false, code
        end
    end)

    if not success then
        logger.err("Crossbill: Exception during sync:", result)
        -- Only show error popup for manual syncs
        if not is_autosync then
            UIManager:show(InfoMessage:new{
                text = _("Sync error: ") .. tostring(result),
                timeout = 5,
            })
        end
    end
end

function CrossbillSync:getFilename(path)
    return path:match("^.+/(.+)$") or path
end

function CrossbillSync:uploadCoverImage(book_id, token)
    -- Extract and upload the book cover image
    -- This function is called after successful highlights sync
    local success, err = pcall(function()
        logger.dbg("Crossbill: Attempting to extract cover for book_id:", book_id)

        -- Get the cover image from the document
        local cover_image = FileManagerBookInfo:getCoverImage(self.ui.document)

        if not cover_image then
            logger.dbg("Crossbill: No cover image available for this document")
            return
        end

        logger.dbg("Crossbill: Cover image extracted, size:", cover_image:getWidth(), "x", cover_image:getHeight())

        -- Save cover to temporary file
        local tmp_cover_path = "/tmp/crossbill_cover_" .. book_id .. ".jpg"
        cover_image:writeToFile(tmp_cover_path)
        logger.dbg("Crossbill: Cover saved to temporary file:", tmp_cover_path)

        -- Read the cover file content
        local cover_file = io.open(tmp_cover_path, "rb")
        if not cover_file then
            logger.err("Crossbill: Failed to open temporary cover file")
            cover_image:free()
            return
        end

        local cover_data = cover_file:read("*all")
        cover_file:close()

        -- Free the cover image from memory
        cover_image:free()

        -- Prepare multipart/form-data upload
        local boundary = "----CrossbillBoundary" .. os.time()
        local body_parts = {}

        -- Add the file part
        table.insert(body_parts, "--" .. boundary)
        table.insert(body_parts, 'Content-Disposition: form-data; name="cover"; filename="cover.jpg"')
        table.insert(body_parts, "Content-Type: image/jpeg")
        table.insert(body_parts, "")
        table.insert(body_parts, cover_data)
        table.insert(body_parts, "--" .. boundary .. "--")

        local body = table.concat(body_parts, "\r\n")

        -- Construct API URL
        local api_url = self.settings.base_url .. "/api/v1/book/" .. book_id .. "/metadata/cover"
        logger.dbg("Crossbill: Uploading cover to", api_url)

        local response_body = {}
        local request = {
            url = api_url,
            method = "POST",
            headers = {
                ["Content-Type"] = "multipart/form-data; boundary=" .. boundary,
                ["Content-Length"] = tostring(#body),
                ["Authorization"] = "Bearer " .. token,
            },
            source = ltn12.source.string(body),
            sink = ltn12.sink.table(response_body),
        }

        -- Use HTTP or HTTPS based on URL scheme
        local code
        if api_url:match("^https://") then
            code = socket.skip(1, https.request(request))
        else
            code = socket.skip(1, http.request(request))
        end
        socketutil:reset_timeout()

        -- Clean up temporary file
        os.remove(tmp_cover_path)

        if code == 200 then
            logger.info("Crossbill: Cover uploaded successfully for book", book_id)
        else
            logger.warn("Crossbill: Failed to upload cover, response code:", code)
        end
    end)

    if not success then
        logger.err("Crossbill: Error uploading cover:", err)
        -- Don't show error to user, cover upload is optional
    end
end

function CrossbillSync:registerEventHandlers()
    -- Event handlers are automatically called by KOReader framework
    -- when methods match the naming pattern on<EventName>
    -- No explicit registration needed
end

function CrossbillSync:onCloseDocument()
    -- Called when user closes the current book
    if self.settings.autosync_enabled then
        logger.info("Crossbill: Auto-syncing on document close")
        self:syncCurrentBook(true)  -- true = autosync (silent mode)
    end
    return false  -- Allow other handlers to process this event
end

function CrossbillSync:onSuspend()
    -- Called when device goes to sleep/suspend (user stops reading)
    if self.settings.autosync_enabled then
        logger.info("Crossbill: Auto-syncing on suspend")
        self:syncCurrentBook(true)  -- true = autosync (silent mode)
    end
    return false  -- Allow other handlers to process this event
end

function CrossbillSync:onExit()
    -- Called when KOReader exits
    if self.settings.autosync_enabled then
        logger.info("Crossbill: Auto-syncing on exit")
        self:syncCurrentBook(true)  -- true = autosync (silent mode)
    end
    return false  -- Allow other handlers to process this event
end

return CrossbillSync
