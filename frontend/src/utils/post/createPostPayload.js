export function buildCreatePostPayload(data) {
  return {
    organization: data.organization,

    platforms: data.platforms,

    platform_content_types:
      data.platform_content_types,

    media: data.media.map((item) => ({
      id: item.id,
      name: item.name,
      mime_type: item.mime_type,
      size: item.size,
      type: item.type,
      file: item.file,
    })),

    caption: data.caption,

    ai: {
      prompt: data.ai_prompt,
      tone: data.ai_tone,
      length: data.ai_length,
      include_emoji:
        data.ai_include_emoji,
      include_hashtags:
        data.ai_include_hashtags,
      include_cta:
        data.ai_include_cta,
    },

    publishing: {
      type: data.publish_type,

      date:
        data.publish_type === "SCHEDULE"
          ? data.publish_date
          : null,

      time:
        data.publish_type === "SCHEDULE"
          ? data.publish_time
          : null,

      timezone:
        data.publish_type === "SCHEDULE"
          ? data.timezone
          : null,
    },
  };
}