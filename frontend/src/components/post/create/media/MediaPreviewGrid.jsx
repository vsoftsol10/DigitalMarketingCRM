import { Grid, Typography } from "@mui/material";

import MediaPreviewItem from "./MediaPreviewItem";
import { TYPOGRAPHY } from "../../../../theme/typography";

export default function MediaPreviewGrid({
  media = [],
  onRemove,
}) {
  if (!media.length) {
    return null;
  }

  return (
    <>
      <Typography
        sx={{
          ...TYPOGRAPHY.inputLabel,
          mb: 2,
        }}
      >
        Uploaded Media ({media.length})
      </Typography>

      <Grid container spacing={2}>
        {media.map((item) => (
          <Grid
            key={item.id}
            size={{
              xs: 12,
              sm: 6,
              md: 4,
            }}
          >
            <MediaPreviewItem
              media={item}
              onRemove={onRemove}
            />
          </Grid>
        ))}
      </Grid>
    </>
  );
}