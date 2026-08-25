import { Stack } from "@mui/material";

import BestTimeItem from "./BestTimeItem";

export default function BestTimeList({
  data = [],
}) {
  return (
    <Stack spacing={1.5}>
      {data.map((item) => (
        <BestTimeItem
          key={item.day}
          item={item}
        />
      ))}
    </Stack>
  );
}