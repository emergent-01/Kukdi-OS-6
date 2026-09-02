import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "./Modal";

const COMPETENCIES = [
  "Leadership", "Ambiguity", "Failure", "Conflict", "Influence",
  "Execution", "Analytical Thinking", "Customer Focus",
];

function Chip({ label, selected, onClick, testId }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testId}
      className={`px-3.5 py-1.5 rounded-full text-sm transition-colors border ${
        selected
          ? "bg-[#D4DDD7] border-[#9DB0A3] text-[#2C2D2B]"
          : "bg-transparent border-[#E2DFD8] text-[#8A8F8C] hover:border-[#D4DDD7]"
      }`}
    >
      {label}
    </button>
  );
}

const emptyDraft = () => ({
  date: new Date().toISOString().slice(0, 10),
  competencies: [],
  company: "",
  feedback: "",
  what_went_well: "",
  to_act_on: "",
});

/**
 * Shared mock-session modal — the single source of truth for logging a mock,
 * reused by People, Dream Offer and Stories. Behaviour and data-testids match
 * the original People modal exactly.
 *
 * Props:
 *  - person: { id, name } | null   (modal is open when person is truthy)
 *  - presetCompetencies: string[]  (pre-selected competency chips)
 *  - onClose: () => void
 *  - onSaved: (personId) => void
 */
export default function MockModal({ person, presetCompetencies = [], onClose, onSaved }) {
  const [draft, setDraft] = useState(emptyDraft());
  const presetKey = (presetCompetencies || []).filter(Boolean).join("|");

  useEffect(() => {
    if (person) {
      setDraft({ ...emptyDraft(), competencies: presetKey ? presetKey.split("|") : [] });
    }
  }, [person, presetKey]);

  const toggleComp = (c) =>
    setDraft((d) => ({
      ...d,
      competencies: d.competencies.includes(c)
        ? d.competencies.filter((x) => x !== c)
        : [...d.competencies, c],
    }));

  const save = async () => {
    if (!person) return;
    await api.createMock({
      person_ids: [person.id],
      date: draft.date ? new Date(draft.date).toISOString() : undefined,
      competencies: draft.competencies,
      company: draft.company || null,
      feedback: draft.feedback || null,
      what_went_well: draft.what_went_well || null,
      to_act_on: draft.to_act_on || null,
    });
    const pid = person.id;
    onClose?.();
    onSaved?.(pid);
  };

  return (
    <Modal open={!!person} onClose={onClose} title={person ? `A mock with ${person.name}` : ""} testId="mock-modal">
      <Field label="When">
        <input
          type="date"
          className={inputClass}
          value={draft.date}
          onChange={(e) => setDraft({ ...draft, date: e.target.value })}
          data-testid="mock-date"
        />
      </Field>
      <Field label="What you practised">
        <div className="flex flex-wrap gap-2">
          {COMPETENCIES.map((c) => (
            <Chip
              key={c}
              label={c}
              selected={draft.competencies.includes(c)}
              onClick={() => toggleComp(c)}
              testId={`mock-competency-chip-${c}`}
            />
          ))}
        </div>
      </Field>
      <Field label="For a company (optional)">
        <input className={inputClass} value={draft.company} onChange={(e) => setDraft({ ...draft, company: e.target.value })} data-testid="mock-company" />
      </Field>
      <Field label="Feedback">
        <textarea className={inputClass} rows={2} value={draft.feedback} onChange={(e) => setDraft({ ...draft, feedback: e.target.value })} data-testid="mock-feedback" />
      </Field>
      <Field label="What went well (optional)">
        <input className={inputClass} value={draft.what_went_well} onChange={(e) => setDraft({ ...draft, what_went_well: e.target.value })} data-testid="mock-what-went-well" />
      </Field>
      <Field label="To act on (optional)">
        <input className={inputClass} value={draft.to_act_on} onChange={(e) => setDraft({ ...draft, to_act_on: e.target.value })} data-testid="mock-to-act-on" />
      </Field>
      <PrimaryButton onClick={save} data-testid="mock-save">Save</PrimaryButton>
    </Modal>
  );
}
