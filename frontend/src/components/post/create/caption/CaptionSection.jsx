// import SectionCard from "../SectionCard";

// import CaptionEditor from "./CaptionEditor";
// import CaptionToolbar from "./CaptionToolbar";
// import CaptionStats from "./CaptionStats";

// export default function CaptionSection() {
//   return (
//     <SectionCard
//       title="Caption"
//       description="Write and refine the caption for your social media post."
//     >
//       <CaptionEditor />

//       <CaptionToolbar />

//       <CaptionStats />
//     </SectionCard>
//   );
// }

import Stack from "@mui/material/Stack";

import SectionCard from "../SectionCard";

import CaptionEditor from "./CaptionEditor";
import CaptionToolbar from "./CaptionToolbar";
import CaptionStats from "./CaptionStats";

export default function CaptionSection() {
  return (
    <SectionCard
      title="Caption"
      description="Write, edit or refine the caption for your post."
    >
      <Stack spacing={1.25}>
        <CaptionEditor />

        <CaptionToolbar />

        <CaptionStats />
      </Stack>
    </SectionCard>
  );
}