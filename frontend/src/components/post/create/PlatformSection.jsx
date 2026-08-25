// import { Grid } from "@mui/material";
// import { useFormContext } from "react-hook-form";

// import SectionCard from "./SectionCard";
// import PlatformCard from "./PlatformCard";

// export default function PlatformSection({
//   platforms = [],
// }) {
//   const { watch, setValue } = useFormContext();

//   const selectedPlatforms =
//     watch("platforms") || [];

//   function togglePlatform(id) {
//     const exists =
//       selectedPlatforms.includes(id);

//     if (exists) {
//       setValue(
//         "platforms",
//         selectedPlatforms.filter(
//           (item) => item !== id
//         ),
//         {
//           shouldDirty: true,
//           shouldValidate: true,
//         }
//       );

//       return;
//     }

//     setValue(
//       "platforms",
//       [...selectedPlatforms, id],
//       {
//         shouldDirty: true,
//         shouldValidate: true,
//       }
//     );
//   }

//   return (
//     <SectionCard
//       title="Platforms"
//       description="Select one or more platforms to publish to."
//     >
//       <Grid
//         container
//         spacing={2}
//       >
//         {platforms.map((platform) => (
//           <Grid
//             key={platform.id}
//             size={{
//               xs: 12,
//               sm: 6,
//               md: 4,
//             }}
//           >
//             <PlatformCard
//               platform={platform}
//               selected={selectedPlatforms.includes(
//                 platform.id
//               )}
//               onClick={() =>
//                 togglePlatform(platform.id)
//               }
//             />
//           </Grid>
//         ))}
//       </Grid>
//     </SectionCard>
//   );
// }



import {
  Grid,
  Typography,
} from "@mui/material";

import { useFormContext } from "react-hook-form";

import SectionCard from "./SectionCard";
import PlatformCard from "./PlatformCard";

import { TYPOGRAPHY } from "../../../theme/typography";

export default function PlatformSection({
  platforms = [],
}) {
  const {
    watch,
    setValue,
    formState: { errors },
  } = useFormContext();

  const selectedPlatforms =
    watch("platforms") || [];

  function togglePlatform(id) {
    const exists =
      selectedPlatforms.includes(id);

    if (exists) {
      setValue(
        "platforms",
        selectedPlatforms.filter(
          (item) => item !== id
        ),
        {
          shouldDirty: true,
          shouldValidate: true,
        }
      );

      return;
    }

    setValue(
      "platforms",
      [...selectedPlatforms, id],
      {
        shouldDirty: true,
        shouldValidate: true,
      }
    );
  }

  return (
    <SectionCard
      title="Social Platforms"
      description="Select the platforms where you want to publish this post."
    >
      <Grid
        container
        spacing={2}
      >
        {platforms.map((platform) => (
          <Grid
            key={platform.id}
            size={{
              xs: 12,
              sm: 6,
              md: 4,
            }}
          >
            <PlatformCard
              platform={platform}
              selected={selectedPlatforms.includes(
                platform.id
              )}
              onClick={() =>
                togglePlatform(platform.id)
              }
            />
          </Grid>
        ))}
      </Grid>

      {errors.platforms && (
        <Typography
          sx={{
            ...TYPOGRAPHY.helperText,
            color: "error.main",
            mt: 1.5,
          }}
        >
          {errors.platforms.message}
        </Typography>
      )}
    </SectionCard>
  );
}