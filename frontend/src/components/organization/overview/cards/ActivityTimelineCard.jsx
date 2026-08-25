// import { Box, Card, CardContent, Stack, Typography } from "@mui/material";

// import FiberManualRecordRoundedIcon from "@mui/icons-material/FiberManualRecordRounded";

// import { TYPOGRAPHY } from "../../../../theme/typography";

// export default function ActivityTimelineCard({ organization }) {
//   // const timeline = organization?.activity_timeline || [];
//   const timeline = organization?.activities || [];

//   return (
//     <Card
//       elevation={0}
//       sx={{
//         border: "1px solid #E2E8F0",
//         borderRadius: "20px",
//       }}
//     >
//       <CardContent
//         sx={{
//           p: 3,
//         }}
//       >
//         {/* Header */}

//         <Typography sx={TYPOGRAPHY.sectionTitle}>Activity Timeline</Typography>

//         <Typography
//           sx={{
//             ...TYPOGRAPHY.sectionDescription,
//             mb: 4,
//           }}
//         >
//           Recent events for this organization
//         </Typography>

//         {/* Empty State */}

//         {timeline.length === 0 ? (
//           <Box
//             sx={{
//               py: 6,
//               display: "flex",
//               justifyContent: "center",
//               alignItems: "center",
//             }}
//           >
//             <Typography
//               sx={{
//                 color: "#94A3B8",
//                 fontSize: 15,
//               }}
//             >
//               No activity yet
//             </Typography>
//           </Box>
//         ) : (
//           <Stack spacing={0}>
//             {timeline.map((item, index) => (
//               <Box
//                 key={item.id}
//                 sx={{
//                   display: "flex",
//                   alignItems: "flex-start",
//                 }}
//               >
//                 {/* Timeline Line */}

//                 <Box
//                   sx={{
//                     width: 28,
//                     display: "flex",
//                     flexDirection: "column",
//                     alignItems: "center",
//                     flexShrink: 0,
//                   }}
//                 >
//                   <FiberManualRecordRoundedIcon
//                     sx={{
//                       fontSize: 14,
//                       color: "#3B82F6",
//                       zIndex: 2,
//                       bgcolor: "#FFFFFF",
//                     }}
//                   />

//                   {index !== timeline.length - 1 && (
//                     <Box
//                       sx={{
//                         width: 2,
//                         flex: 1,
//                         minHeight: 62,
//                         bgcolor: "#E2E8F0",
//                       }}
//                     />
//                   )}
//                 </Box>

//                 {/* Content */}

//                 <Box
//                   sx={{
//                     ml: 2,
//                     pb: 3,
//                   }}
//                 >
//                   <Typography
//                     sx={{
//                       fontSize: 18,
//                       fontWeight: 600,
//                       color: "#1E293B",
//                     }}
//                   >
//                     {item.title || "-"}
//                   </Typography>

//                   <Typography
//                     sx={{
//                       mt: 0.5,
//                       color: "#64748B",
//                     }}
//                   >
//                     {item.description || "-"}
//                   </Typography>

//                   <Typography
//                     sx={{
//                       mt: 0.5,
//                       fontSize: 14,
//                       color: "#94A3B8",
//                     }}
//                   >
//                     {item.created_at
//                       ? new Date(item.created_at).toLocaleString("en-US", {
//                           month: "short",
//                           day: "numeric",
//                           year: "numeric",
//                           hour: "numeric",
//                           minute: "2-digit",
//                         })
//                       : "-"}
//                   </Typography>
//                 </Box>
//               </Box>
//             ))}
//           </Stack>
//         )}
//       </CardContent>
//     </Card>
//   );
// }

import { Box, Card, CardContent, Typography } from "@mui/material";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function ActivityTimelineCard({ organization }) {
  const activities = Array.isArray(organization?.activities)
    ? organization.activities
    : [];

  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "20px",
      }}
    >
      <CardContent
        sx={{
          p: 3,
        }}
      >
        {/* Header */}

        <Typography sx={TYPOGRAPHY.sectionTitle}>Activity Timeline</Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mb: 4,
          }}
        >
          Recent events for this organization
        </Typography>

        {/* Empty State */}

        {activities.length === 0 && (
          <Box
            sx={{
              py: 6,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
            }}
          >
            <Typography
              sx={{
                color: "#94A3B8",
                fontSize: 15,
              }}
            >
              No activity yet
            </Typography>
          </Box>
        )}

        {/* Timeline */}

        {activities.length > 0 && (
          <Box>
            {activities.map((activity, index) => (
              <Box
                key={activity.id || `${activity.type}-${index}`}
                sx={{
                  display: "flex",
                  gap: 2,
                  pb: index === activities.length - 1 ? 0 : 3,
                }}
              >
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    mt: 0.8,
                    borderRadius: "50%",
                    bgcolor: "#2563EB",
                    flexShrink: 0,
                  }}
                />

                <Box>
                  <Typography
                    sx={{
                      fontSize: 16,
                      fontWeight: 600,
                      color: "#1E293B",
                    }}
                  >
                    {activity.title || "-"}
                  </Typography>

                  <Typography
                    sx={{
                      mt: 0.5,
                      color: "#64748B",
                    }}
                  >
                    {activity.description || "-"}
                  </Typography>

                  {activity.created_at && (
                    <Typography
                      sx={{
                        mt: 0.5,
                        fontSize: 13,
                        color: "#94A3B8",
                      }}
                    >
                      {new Date(activity.created_at).toLocaleString("en-US", {
                        month: "short",
                        day: "numeric",
                        year: "numeric",
                        hour: "numeric",
                        minute: "2-digit",
                      })}
                    </Typography>
                  )}
                </Box>
              </Box>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
