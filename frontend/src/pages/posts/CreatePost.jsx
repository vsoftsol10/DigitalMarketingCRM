
// import { FormProvider, useForm } from "react-hook-form";
// import { zodResolver } from "@hookform/resolvers/zod";

// import { Box, Grid } from "@mui/material";

// import { useEffect, useState } from "react";

// import postService from "../../services/post.service";

// import CreatePostHeader from "../../components/post/create/CreatePostHeader";

// import OrganizationSection from "../../components/post/create/OrganizationSection";
// import PlatformSection from "../../components/post/create/PlatformSection";
// import ContentTypeSection from "../../components/post/create/ContentTypeSection";
// import MediaUploadSection from "../../components/post/create/media/MediaUploadSection";
// import AICaptionSection from "../../components/post/create/AICaptionSection";
// import CaptionSection from "../../components/post/create/CaptionSection";

// import LivePreviewSection from "../../components/post/create/LivePreviewSection";
// import PublishingSection from "../../components/post/create/PublishingSection";

// import { createPostDefaultValues } from "../../constants/forms/createPostDefaultValues";

// import { createPostSchema } from "../../validation/createPost.schema";

// import { buildCreatePostPayload } from "../../utils/post/createPostPayload";

// export default function CreatePost() {
//   const methods = useForm({
//     defaultValues: createPostDefaultValues,

//     resolver: zodResolver(createPostSchema),

//     mode: "onSubmit",
//   });

//   const [createPostData, setCreatePostData] =
//     useState(null);

//   useEffect(() => {
//     loadData();
//   }, []);

//   async function loadData() {
//     const response =
//       await postService.getCreatePostData();

//     setCreatePostData(response);
//   }

//   async function handleCreatePost(data) {
//     const payload =
//       buildCreatePostPayload(data);

//     console.log(
//       "Create Post Payload:",
//       payload
//     );

//     // Backend API will be connected here.
//     //
//     // await postService.createPost(payload);
//   }

//   function handleValidationError(errors) {
//     console.log(
//       "Create Post Validation Errors:",
//       errors
//     );
//   }

//   if (!createPostData) {
//     return null;
//   }

//   return (
//     <FormProvider {...methods}>
//       <Box
//         component="form"
//         onSubmit={methods.handleSubmit(
//           handleCreatePost,
//           handleValidationError
//         )}
//       >
//         <Grid
//           container
//           spacing={4}
//           alignItems="flex-start"
//         >
//           {/* LEFT */}

//           <Grid
//             size={{
//               xs: 12,
//               lg: 8,
//             }}
//           >
//             <Box
//               sx={{
//                 display: "flex",
//                 flexDirection: "column",
//                 gap: 4,
//               }}
//             >
//               <OrganizationSection
//                 organizations={
//                   createPostData.organizations
//                 }
//               />

//               <PlatformSection
//                 platforms={
//                   createPostData.platforms
//                 }
//               />

//               <ContentTypeSection
//                 platforms={
//                   createPostData.platforms
//                 }
//               />

//               <MediaUploadSection
//                 config={createPostData.media}
//               />

//               <AICaptionSection />

//               <CaptionSection />
//             </Box>
//           </Grid>

//           {/* RIGHT */}

//           <Grid
//             size={{
//               xs: 12,
//               lg: 4,
//             }}
//           >
//             <Box
//               sx={{
//                 position: {
//                   lg: "sticky",
//                 },

//                 top: 24,

//                 display: "flex",
//                 flexDirection: "column",
//                 gap: 3,
//               }}
//             >
//               <LivePreviewSection
//                 organizations={
//                   createPostData.organizations
//                 }
//                 platforms={
//                   createPostData.platforms
//                 }
//               />

//               <PublishingSection />
//             </Box>
//           </Grid>
//         </Grid>
//       </Box>
//     </FormProvider>
//   );
// }

import { FormProvider, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { Box, Grid } from "@mui/material";

import { useEffect, useState } from "react";

import postService from "../../services/post.service";

import OrganizationSection from "../../components/post/create/OrganizationSection";
import PlatformSection from "../../components/post/create/PlatformSection";
import ContentTypeSection from "../../components/post/create/ContentTypeSection";
import MediaUploadSection from "../../components/post/create/media/MediaUploadSection";
import AICaptionSection from "../../components/post/create/AICaptionSection";
import CaptionSection from "../../components/post/create/CaptionSection";

import LivePreviewSection from "../../components/post/create/LivePreviewSection";
import PublishingSection from "../../components/post/create/PublishingSection";

import { createPostDefaultValues } from "../../constants/forms/createPostDefaultValues";
import { createPostSchema } from "../../validation/createPost.schema";

import { buildCreatePostPayload } from "../../utils/post/createPostPayload";

export default function CreatePost() {
  const methods = useForm({
    defaultValues: createPostDefaultValues,

    resolver: zodResolver(createPostSchema),

    mode: "onSubmit",
  });

  const [createPostData, setCreatePostData] =
    useState(null);

  const [isSubmitting, setIsSubmitting] =
    useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    const response =
      await postService.getCreatePostData();

    setCreatePostData(response);
  }

  async function handleCreatePost(data) {
    try {
      setIsSubmitting(true);

      const payload =
        buildCreatePostPayload(data);

      console.log(
        "Create Post Payload:",
        payload
      );

      /*
       * Backend API will be connected here.
       *
       * await postService.createPost(payload);
       */

      if (data.publish_type === "NOW") {
        console.log(
          "Post should be published now."
        );
      }

      if (data.publish_type === "SCHEDULE") {
        console.log(
          "Post should be scheduled."
        );
      }

      if (data.publish_type === "DRAFT") {
        console.log(
          "Post should be saved as draft."
        );
      }
    } catch (error) {
      console.error(
        "Create post failed:",
        error
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  function handleValidationError(errors) {
    console.log(
      "Create Post Validation Errors:",
      errors
    );
  }

  if (!createPostData) {
    return null;
  }

  return (
    <FormProvider {...methods}>
      <Box
        component="form"
        onSubmit={methods.handleSubmit(
          handleCreatePost,
          handleValidationError
        )}
      >
        <Grid
          container
          spacing={4}
          alignItems="flex-start"
        >
          {/* LEFT */}

          <Grid
            size={{
              xs: 12,
              lg: 8,
            }}
          >
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                gap: 4,
              }}
            >
              <OrganizationSection
                organizations={
                  createPostData.organizations
                }
              />

              <PlatformSection
                platforms={
                  createPostData.platforms
                }
              />

              <ContentTypeSection
                platforms={
                  createPostData.platforms
                }
              />

              <MediaUploadSection
                config={createPostData.media}
              />

              <AICaptionSection />

              <CaptionSection />
            </Box>
          </Grid>

          {/* RIGHT */}

          <Grid
            size={{
              xs: 12,
              lg: 4,
            }}
          >
            <Box
              sx={{
                position: {
                  lg: "sticky",
                },

                top: 24,

                display: "flex",
                flexDirection: "column",
                gap: 3,
              }}
            >
              <LivePreviewSection
                organizations={
                  createPostData.organizations
                }
                platforms={
                  createPostData.platforms
                }
              />

              <PublishingSection
                loading={isSubmitting}
              />
            </Box>
          </Grid>
        </Grid>
      </Box>
    </FormProvider>
  );
}