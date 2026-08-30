"""
Unit tests for Custom Action schema and contract validation.
"""

import unittest
from lumen.core.actions.manifest import ActionDefinition
from lumen.core.actions.validator import ActionValidator, IssueSeverity


class TestActionsValidator(unittest.TestCase):

    def test_valid_action_passes(self):
        act = ActionDefinition(
            id="valid-action",
            name="Valid Action",
            exec=["echo", "test"],
        )
        issues = ActionValidator.validate_action(act)
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        self.assertEqual(len(errors), 0)
        self.assertTrue(act.is_valid)

    def test_missing_fields_fail(self):
        act = ActionDefinition(
            id="",
            name="",
            exec=[],
        )
        issues = ActionValidator.validate_action(act)
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR]
        self.assertGreaterEqual(len(errors), 2)
        self.assertFalse(act.is_valid)

    def test_invalid_id_format(self):
        act = ActionDefinition(
            id="invalid id with spaces!",
            name="Action",
            exec=["echo"],
        )
        issues = ActionValidator.validate_action(act)
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR and i.field == "id"]
        self.assertEqual(len(errors), 1)

    def test_duplicate_ids_in_collection(self):
        act1 = ActionDefinition(id="dup-id", name="Action 1", exec=["echo"])
        act2 = ActionDefinition(id="dup-id", name="Action 2", exec=["echo"])
        issues = ActionValidator.validate_action_collection([act1, act2])
        errors = [i for i in issues if i.severity == IssueSeverity.ERROR and "Duplicate" in i.message]
        self.assertEqual(len(errors), 1)


if __name__ == "__main__":
    unittest.main()
