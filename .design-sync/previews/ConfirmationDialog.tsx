import { ConfirmationDialog } from "crossbill-frontend";

export const DeleteConfirmation = () => (
  <ConfirmationDialog
    open
    onClose={() => {}}
    onConfirm={() => {}}
    title="Delete highlight?"
    message="This will permanently remove the highlight and any flashcards generated from it. This action cannot be undone."
    confirmText="Delete"
    cancelText="Cancel"
    confirmColor="error"
  />
);

export const SaveConfirmation = () => (
  <ConfirmationDialog
    open
    onClose={() => {}}
    onConfirm={() => {}}
    title="Save changes?"
    message="Your edits to this note will be saved."
    confirmText="Save"
    confirmColor="primary"
  />
);
