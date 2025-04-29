"""
Field definitions and validation rules for service report processing.
This module centralizes all field names, alternatives, and related utilities.
"""

# Required fields that must be present in markdown files
REQUIRED_FIELDS = [
    "**Date of service:**",
    "**Technician name:**",
    "**Customer point of contact:**",
    "**Description of problem:**",
    "**Description of work performed:**",
    "**Issue resolved?**",
    "**Next steps?**"
]

# Alternative acceptable field labels
FIELD_ALTERNATIVES = {
    "**Customer point of contact:**": [
        "**Customer points of contact:**",  # Plural form
        "**Client contact:**",
        "**Contact person:**",
        "**Point of contact:**",
        "**Customer contact:**",
        # Variants with colon outside
        "**Customer point of contact**:",
        "**Customer points of contact**:",
        "**Client contact**:",
        "**Contact person**:",
        "**Point of contact**:",
        "**Customer contact**:",
    ],
    
    "**Description of problem:**": [
        "**Description of problems:**",  # Simple plural
        "**Description of problems/requests:**",
        "**Problems and requests:**",
        "**Issues reported:**",
        "**Problems encountered:**",
        "**Service request:**",
        "**Reported issue(s):**",
        # Variants with colon outside
        "**Description of problem**:",
        "**Description of problems**:",  # Simple plural with colon outside
        "**Description of problems/requests**:",
        "**Problems and requests**:",
        "**Issues reported**:",
        "**Problems encountered**:",
        "**Service request**:",
        "**Reported issue(s)**:",
    ],
    
    "**Issue resolved?**": [
        "**Issues resolved?**",  # Added plural form
        "**Issue(s) resolved?**",
        "**Problem resolved?**",
        "**Resolution status:**",
        "**Resolved?**",
        # Variants with question mark outside
        "**Issue resolved**?",
        "**Issues resolved**?",  # Added plural form with question mark outside
        "**Issue(s) resolved**?",
        "**Problem resolved**?",
    ],
    
    "**Next steps?**": [
        "**Next steps:**",
        "**Future actions:**",
        "**Follow-up required:**",
        "**Follow-up actions:**",
        "**Recommended next steps:**",
        # Variants with question mark outside
        "**Next steps**?",
        "**Future actions**?",
        "**Follow-up required**?",
        "**Follow-up actions**?",
        "**Recommended next steps**?",
    ],
    
    "**Date of service:**": [
        "**Service date:**",
        "**Date:**",
        "**Date of visit:**",
        # Variants with colon outside
        "**Date of service**:",
        "**Service date**:",
        "**Date**:",
        "**Date of visit**:",
    ],
    
    "**Technician name:**": [
        "**Technician:**",
        "**Tech name:**",
        "**Service technician:**",
        # Variants with colon outside
        "**Technician name**:",
        "**Technician**:",
        "**Tech name**:",
        "**Service technician**:",
    ],
    
    "**Description of work performed:**": [
        "**Work performed:**",
        "**Service performed:**",
        "**Actions taken:**",
        "**Work completed:**",
        # Variants with colon outside
        "**Description of work performed**:",
        "**Work performed**:",
        "**Service performed**:",
        "**Actions taken**:",
        "**Work completed**:",
    ]
}

def get_plain_field_name(field):
    """Extract the plain field name without markdown formatting or punctuation."""
    return field.replace('**', '').replace(':', '').replace('?', '')