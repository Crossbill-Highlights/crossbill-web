import {
  IconButtonWithTooltip,
  EditIcon,
  DeleteIcon,
  CopyIcon,
  MoreIcon,
} from "crossbill-frontend";

const noop = () => {};

export const EditHighlight = () => (
  <IconButtonWithTooltip
    title="Edit highlight"
    ariaLabel="Edit highlight"
    onClick={noop}
    icon={<EditIcon fontSize="small" />}
  />
);

export const DeleteDisabled = () => (
  <IconButtonWithTooltip
    title="Delete highlight"
    ariaLabel="Delete highlight"
    onClick={noop}
    disabled
    icon={<DeleteIcon fontSize="small" />}
  />
);

export const InAToolbar = () => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      gap: 4,
      padding: "4px 8px",
      border: "1px solid #e7e5e4",
      borderRadius: 8,
    }}
  >
    <IconButtonWithTooltip
      title="Copy quote"
      ariaLabel="Copy quote"
      onClick={noop}
      icon={<CopyIcon fontSize="small" />}
    />
    <IconButtonWithTooltip
      title="Edit note"
      ariaLabel="Edit note"
      onClick={noop}
      icon={<EditIcon fontSize="small" />}
    />
    <IconButtonWithTooltip
      title="More actions"
      ariaLabel="More actions"
      onClick={noop}
      icon={<MoreIcon fontSize="small" />}
    />
  </div>
);
