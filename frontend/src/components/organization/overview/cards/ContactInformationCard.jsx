import { Box, Card, CardContent, Grid, Stack, Typography } from "@mui/material";

import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import PhoneOutlinedIcon from "@mui/icons-material/PhoneOutlined";
import LocationOnOutlinedIcon from "@mui/icons-material/LocationOnOutlined";

import { TYPOGRAPHY } from "../../../../theme/typography";

export default function ContactInformationCard({ organization }) {
  // const contactInformation = [
  //   {
  //     icon: PersonOutlineOutlinedIcon,
  //     label: "Contact Name",
  //     value: organization.contact,
  //   },
  //   {
  //     icon: EmailOutlinedIcon,
  //     label: "Email",
  //     value: organization.email,
  //   },
  //   {
  //     icon: PhoneOutlinedIcon,
  //     label: "Phone",
  //     value: organization.phone,
  //   },
  //   {
  //     icon: LocationOnOutlinedIcon,
  //     label: "Location",
  //     value: organization.location,
  //   },
  // ];

  const contactInformation = [
    {
      icon: PersonOutlineOutlinedIcon,
      label: "Contact Name",
      value: organization?.contact_name || "-",
    },
    {
      icon: EmailOutlinedIcon,
      label: "Email",
      value: organization?.contact_email || "-",
    },
    {
      icon: PhoneOutlinedIcon,
      label: "Phone",
      value: organization?.contact_phone || "-",
    },
    {
      icon: LocationOnOutlinedIcon,
      label: "Location",
      value: organization?.location || "-",
    },
  ];
  return (
    <Card
      elevation={0}
      sx={{
        border: "1px solid #E2E8F0",
        borderRadius: "22px",
      }}
    >
      <CardContent sx={{ p: 4 }}>
        {/* Header */}

        <Typography sx={TYPOGRAPHY.sectionTitle}>
          Contact Information
        </Typography>

        <Typography
          sx={{
            ...TYPOGRAPHY.sectionDescription,
            mt: 0.5,
            mb: 4,
          }}
        >
          Primary contact details
        </Typography>

        {/* Content */}

        <Grid container spacing={4}>
          {contactInformation.map((item) => {
            const Icon = item.icon;

            return (
              <Grid
                key={item.label}
                size={{
                  xs: 12,
                  md: 6,
                }}
              >
                <Stack direction="row" spacing={2} alignItems="center">
                  <Icon
                    sx={{
                      fontSize: 20,
                      color: "#94A3B8",
                    }}
                  />

                  <Box>
                    <Typography
                      sx={{
                        fontSize: 13,
                        color: "#94A3B8",
                      }}
                    >
                      {item.label}
                    </Typography>

                    <Typography
                      sx={{
                        ...TYPOGRAPHY.body,
                        mt: 0.4,
                        fontWeight: 500,
                      }}
                    >
                      {item.value || "-"}
                    </Typography>
                  </Box>
                </Stack>
              </Grid>
            );
          })}
        </Grid>
      </CardContent>
    </Card>
  );
}
