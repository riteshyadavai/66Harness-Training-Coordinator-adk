package adf.org.training_coordinator.actions

import future.keywords.if
import future.keywords.in

# Drafts-only: no send/execute; tracker remains read-only.

default allow_send := false
default allow_tracker_write := false
default allow_draft := false
default require_hitl := true

allow_draft if {
  input.requireConfirmation == true
  data.training.drafts_only == true
}

require_hitl if {
  input.action in {"draft_email", "draft_teams_message", "draft_session_invite", "reschedule_session_invite", "cancel_session_invite"}
}

allow_send if {
  false
}

allow_tracker_write if {
  data.training.tracker_writes_allowed == true
}
