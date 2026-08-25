import {
  MOCK_DM_AUTOMATIONS,
  MOCK_INSTAGRAM_ACCOUNTS,
  MOCK_INSTAGRAM_CONTENT,
} from "../data/dmAutomationData";

const MOCK_DELAY = 400;

/*
 * Temporary in-memory data store.
 *
 * This is only for the UI development phase.
 * Later this store will be replaced by Django REST API.
 */
let automationStore = [...MOCK_DM_AUTOMATIONS];

const wait = (ms) =>
  new Promise((resolve) => {
    setTimeout(resolve, ms);
  });

const findOrganization = (organizationId) => {
  return MOCK_INSTAGRAM_ACCOUNTS.find(
    (account) => account.id === organizationId,
  );
};

const findContent = (contentId) => {
  return MOCK_INSTAGRAM_CONTENT.find((content) => content.id === contentId);
};

const buildAutomationResponse = (automationId, payload) => {
  const organization = findOrganization(payload.organizationId);

  const content = findContent(payload.contentId);

  if (!organization) {
    throw new Error("Selected Instagram account was not found.");
  }

  if (!content) {
    throw new Error("Selected Instagram content was not found.");
  }

  return {
    id: automationId,

    name: payload.name,

    organizationId: payload.organizationId,
    organization: organization.organization,
    username: organization.username,

    contentId: payload.contentId,
    contentType: payload.contentType,
    contentTitle: content.title,
    contentDate: content.publishedAt,

    triggerType: payload.triggerType,
    triggerValue: payload.triggerValue,

    replyMessage: payload.replyMessage,

    status: payload.status,
  };
};

const dmAutomationService = {
  // ==========================================================
  // GET ALL AUTOMATIONS
  // ==========================================================

  async getAutomations() {
    await wait(MOCK_DELAY);

    return [...automationStore];
  },

  // ==========================================================
  // GET SINGLE AUTOMATION
  // ==========================================================

  async getAutomation(automationId) {
    await wait(MOCK_DELAY);

    return (
      automationStore.find((automation) => automation.id === automationId) ||
      null
    );
  },

  // ==========================================================
  // CREATE AUTOMATION
  // ==========================================================

  async createAutomation(payload) {
    await wait(MOCK_DELAY);

    const automationId = `dma_${Date.now()}`;

    const automation = buildAutomationResponse(automationId, payload);

    automationStore = [automation, ...automationStore];

    return automation;
  },

  // ==========================================================
  // UPDATE AUTOMATION
  // ==========================================================

  async updateAutomation(automationId, payload) {
    await wait(MOCK_DELAY);

    const existingAutomation = automationStore.find(
      (automation) => automation.id === automationId,
    );

    if (!existingAutomation) {
      throw new Error("Automation not found.");
    }

    const updatedAutomation = buildAutomationResponse(automationId, payload);

    automationStore = automationStore.map((automation) =>
      automation.id === automationId ? updatedAutomation : automation,
    );

    return updatedAutomation;
  },

  // ==========================================================
  // TOGGLE AUTOMATION STATUS
  // ==========================================================

  async toggleAutomationStatus(automationId, status) {
    await wait(MOCK_DELAY);

    const existingAutomation = automationStore.find(
      (automation) => automation.id === automationId,
    );

    if (!existingAutomation) {
      throw new Error("Automation not found.");
    }

    if (status !== "active" && status !== "inactive") {
      throw new Error("Invalid automation status.");
    }

    const updatedAutomation = {
      ...existingAutomation,
      status,
    };

    automationStore = automationStore.map((automation) =>
      automation.id === automationId ? updatedAutomation : automation,
    );

    return updatedAutomation;
  },
};

export default dmAutomationService;
