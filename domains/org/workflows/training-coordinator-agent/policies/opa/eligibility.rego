package adf.org.training_coordinator

import future.keywords.if
import future.keywords.in

# Blueprint policy: wire OPA at runtime. Tenure math stays in
# logic_tools.py; pass tenure_days + program on input.

default allow_auto_enroll := false
default require_hitl := true
default eligibility_decision := "hitl_required"

program := data.training.programs[input.program]

in_tenure_window if {
  input.tenure_days >= program.min_tenure_days
  input.tenure_days <= program.max_tenure_days
}

allow_auto_enroll if {
  in_tenure_window
  input.cohort_open == true
  input.exception != true
  data.training.hitl_required_default == false
}

require_hitl if {
  not allow_auto_enroll
}

require_hitl if {
  input.exception == true
  data.training.director_approval_for_exceptions == true
}

require_hitl if {
  input.cohort_open == false
  program.hold_when_cohort_closed == true
}

eligibility_decision := "auto_enroll" if allow_auto_enroll
eligibility_decision := "ineligible" if {
  input.tenure_days < program.min_tenure_days
}
eligibility_decision := "ineligible" if {
  input.tenure_days > program.max_tenure_days
}
eligibility_decision := "hold_next_cycle" if {
  input.cohort_open == false
  program.hold_when_cohort_closed == true
}
eligibility_decision := "hitl_required" if require_hitl
