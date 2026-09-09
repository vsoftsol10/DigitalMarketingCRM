def get_organization_billing_recipient(
    organization,
):
    """
    Return the primary organization contact used
    for subscription transactional emails.
    """

    contact = organization.contacts.filter(
        is_deleted=False,
        is_primary=True,
    ).first()

    if not contact or not contact.email:
        return None, ""

    return (
        contact.email,
        contact.name or "",
    )
