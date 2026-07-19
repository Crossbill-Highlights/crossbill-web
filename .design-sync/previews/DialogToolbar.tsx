import {
  DialogToolbar,
  IconButtonWithTooltip,
  EditIcon,
  DeleteIcon,
  CopyIcon,
} from "crossbill-frontend";

const noop = () => {};

export const HighlightActions = () => (
  <div style={{ width: 320 }}>
    <DialogToolbar>
      <IconButtonWithTooltip
        title="Edit highlight"
        onClick={noop}
        icon={<EditIcon fontSize="small" />}
      />
      <IconButtonWithTooltip
        title="Copy quote"
        onClick={noop}
        icon={<CopyIcon fontSize="small" />}
      />
      <IconButtonWithTooltip
        title="Delete highlight"
        onClick={noop}
        icon={<DeleteIcon fontSize="small" />}
      />
    </DialogToolbar>
  </div>
);

export const AboveContent = () => (
  <div style={{ width: 360 }}>
    <DialogToolbar sx={{ mb: 1 }}>
      <IconButtonWithTooltip
        title="Edit note"
        onClick={noop}
        icon={<EditIcon fontSize="small" />}
      />
      <IconButtonWithTooltip
        title="Delete note"
        onClick={noop}
        icon={<DeleteIcon fontSize="small" />}
      />
    </DialogToolbar>
    <div
      style={{
        fontFamily: '"Lora", Georgia, serif',
        fontSize: 14,
        lineHeight: 1.6,
        color: "#43311E",
        padding: "10px 14px",
        border: "1px solid #e7e5e4",
        borderRadius: 8,
      }}
    >
      Hemingway’s spare prose lets the silence between the old man and the boy
      carry the weight of the story.
    </div>
  </div>
);
