import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Trash2, Check } from "lucide-react";
import { api, formatDay } from "../lib/api";
import { Modal, Field, inputClass, PrimaryButton } from "../components/Modal";

const COMPETENCIES = [
  "Leadership", "Ambiguity", "Failure", "Conflict", "Influence",
  "Execution", "Analytical Thinking", "Customer Focus",
];

const ease = [0.22, 1, 0.36, 1];
const fade = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, ease },
};

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

export default function People() {
  const [people, setPeople] = useState([]);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", relation: "", company: "", birthday: "", notes: "" });

  const [expandedId, setExpandedId] = useState(null);
  const [mocksBy, setMocksBy] = useState({}); // personId -> [mocks]

  const [strengthsFor, setStrengthsFor] = useState(null); // person
  const [strengthsDraft, setStrengthsDraft] = useState({ strengths: [], note: "" });

  const [mockFor, setMockFor] = useState(null); // person
  const emptyMock = { date: new Date().toISOString().slice(0, 10), competencies: [], company: "", feedback: "", what_went_well: "", to_act_on: "" };
  const [mockDraft, setMockDraft] = useState(emptyMock);

  const load = () => api.people().then((d) => setPeople(d.people || []));
  useEffect(() => { load(); }, []);

  const add = async () => {
    if (!form.name.trim()) return;
    await api.createPerson(form);
    setOpen(false);
    setForm({ name: "", relation: "", company: "", birthday: "", notes: "" });
    load();
  };

  const toggleCircle = async (p) => {
    await api.updatePerson(p.id, { prep_group: !p.prep_group });
    load();
  };

  const loadMocks = async (personId) => {
    const d = await api.listMocks(personId);
    setMocksBy((m) => ({ ...m, [personId]: d.mocks || [] }));
  };

  const toggleExpand = (p) => {
    if (expandedId === p.id) {
      setExpandedId(null);
    } else {
      setExpandedId(p.id);
      loadMocks(p.id);
    }
  };

  const openStrengths = (p) => {
    setStrengthsDraft({ strengths: p.strengths || [], note: p.strength_note || "" });
    setStrengthsFor(p);
  };
  const toggleStrength = (c) => {
    setStrengthsDraft((d) => ({
      ...d,
      strengths: d.strengths.includes(c) ? d.strengths.filter((x) => x !== c) : [...d.strengths, c],
    }));
  };
  const saveStrengths = async () => {
    await api.updatePerson(strengthsFor.id, { strengths: strengthsDraft.strengths, strength_note: strengthsDraft.note });
    setStrengthsFor(null);
    load();
  };

  const openMock = (p) => {
    setMockDraft(emptyMock);
    setMockFor(p);
  };
  const toggleMockComp = (c) => {
    setMockDraft((d) => ({
      ...d,
      competencies: d.competencies.includes(c) ? d.competencies.filter((x) => x !== c) : [...d.competencies, c],
    }));
  };
  const saveMock = async () => {
    const payload = {
      person_ids: [mockFor.id],
      date: mockDraft.date ? new Date(mockDraft.date).toISOString() : undefined,
      competencies: mockDraft.competencies,
      company: mockDraft.company || null,
      feedback: mockDraft.feedback || null,
      what_went_well: mockDraft.what_went_well || null,
      to_act_on: mockDraft.to_act_on || null,
    };
    await api.createMock(payload);
    const pid = mockFor.id;
    setMockFor(null);
    setExpandedId(pid);
    loadMocks(pid);
  };

  const markActed = async (mockId, personId) => {
    await api.updateMock(mockId, { acted: true });
    loadMocks(personId);
  };

  const circle = people.filter((p) => p.prep_group === true);
  const rest = people.filter((p) => p.prep_group !== true);

  const renderPerson = (p, member) => {
    const mocks = mocksBy[p.id] || [];
    const isOpen = expandedId === p.id;
    return (
      <div className="flex gap-6 group" data-testid={`person-${p.id}`}>
        <div className="h-14 w-14 rounded-full bg-[#D4DDD7] shrink-0 flex items-center justify-center font-editorial text-2xl text-[#2C2D2B]">
          {p.name.charAt(0)}
        </div>
        <div className="flex-1 border-b border-[#E2DFD8] pb-10">
          <div className="flex items-baseline justify-between">
            <button
              onClick={() => toggleExpand(p)}
              data-testid={`person-expand-${p.id}`}
              className="font-editorial text-3xl text-[#2C2D2B] text-left hover:text-[#5C605A] transition-colors"
            >
              {p.name}
            </button>
            <div className="flex items-center gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => toggleCircle(p)}
                data-testid={`person-prep-toggle-${p.id}`}
                className="text-xs tracking-[0.15em] uppercase text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors"
              >
                {member ? "Remove from circle" : "Add to prep circle"}
              </button>
              <button
                onClick={async () => { await api.deletePerson(p.id); load(); }}
                data-testid={`person-delete-${p.id}`}
                className="text-[#8A8F8C] hover:text-[#a9564a]"
              >
                <Trash2 size={15} strokeWidth={1.5} />
              </button>
            </div>
          </div>
          <p className="text-sm text-[#8A8F8C] mt-1">
            {[p.relation, p.company, p.birthday].filter(Boolean).join(" · ")}
          </p>
          {p.notes && <p className="text-[#5C605A] mt-4 leading-relaxed max-w-xl">{p.notes}</p>}

          {member && (
            <div className="mt-5">
              {(p.strengths?.length > 0 || p.strength_note) ? (
                <div className="group/str">
                  <div className="flex flex-wrap items-center gap-2">
                    {(p.strengths || []).map((s) => (
                      <span key={s} className="px-3 py-1 rounded-full text-sm bg-[#D4DDD7] text-[#2C2D2B]">{s}</span>
                    ))}
                    <button
                      onClick={() => openStrengths(p)}
                      data-testid={`person-strengths-edit-${p.id}`}
                      className="text-xs tracking-[0.15em] uppercase text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors ml-1"
                    >
                      Edit
                    </button>
                  </div>
                  {p.strength_note && <p className="text-sm text-[#8A8F8C] mt-2 italic">{p.strength_note}</p>}
                </div>
              ) : (
                <button
                  onClick={() => openStrengths(p)}
                  data-testid={`person-strengths-edit-${p.id}`}
                  className="text-xs tracking-[0.15em] uppercase text-[#8A8F8C] hover:text-[#2C2D2B] transition-colors"
                >
                  Note what they’re strong at
                </button>
              )}
            </div>
          )}

          <AnimatePresence>
            {isOpen && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.5, ease }}
                className="overflow-hidden"
                data-testid={`person-detail-${p.id}`}
              >
                <div className="mt-8">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">Practice together</span>
                    <button
                      onClick={() => openMock(p)}
                      data-testid={`mock-log-open-${p.id}`}
                      className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors"
                    >
                      <Plus size={14} strokeWidth={1.5} /> Log a mock
                    </button>
                  </div>
                  {mocks.length === 0 ? (
                    <p className="text-[#8A8F8C]">No mocks logged with {p.name} yet.</p>
                  ) : (
                    <div className="space-y-5">
                      {mocks.map((m) => (
                        <div key={m.id} data-testid={`mock-${m.id}`} className="group/mock">
                          <p className="text-[#5C605A] leading-relaxed">
                            <span className="text-[#8A8F8C]">{formatDay(m.date)}</span>
                            {m.who?.length ? <span className="text-[#8A8F8C]"> · {m.who.join(", ")}</span> : null}
                            {m.company ? <span className="text-[#8A8F8C]"> · {m.company}</span> : null}
                            {m.feedback ? <span> — {m.feedback}</span> : null}
                          </p>
                          {m.what_went_well && (
                            <p className="text-sm text-[#8A8F8C] mt-1">Went well · {m.what_went_well}</p>
                          )}
                          {m.to_act_on && !m.acted && (
                            <div className="flex items-center gap-3 mt-1">
                              <span className="text-sm text-[#8A8F8C] italic">Still to act on · {m.to_act_on}</span>
                              <button
                                onClick={() => markActed(m.id, p.id)}
                                data-testid={`mock-mark-acted-${m.id}`}
                                className="opacity-0 group-hover/mock:opacity-100 transition-opacity text-xs tracking-[0.15em] uppercase text-[#8A8F8C] hover:text-[#2C2D2B]"
                              >
                                Mark done
                              </button>
                            </div>
                          )}
                          {m.to_act_on && m.acted && (
                            <p className="text-sm text-[#9DB0A3] mt-1 flex items-center gap-1.5">
                              <Check size={13} strokeWidth={1.5} /> Acted on · {m.to_act_on}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  };

  return (
    <div data-testid="people-page">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C]">People</span>
        <button onClick={() => setOpen(true)} data-testid="add-person-btn" className="flex items-center gap-1.5 text-sm text-[#5C605A] hover:text-[#2C2D2B] transition-colors">
          <Plus size={15} strokeWidth={1.5} /> Add
        </button>
      </div>
      <h1 className="font-editorial text-5xl md:text-6xl text-[#2C2D2B] mb-16">The people who matter</h1>

      {circle.length > 0 && (
        <motion.section {...fade} className="mb-20" data-testid="prep-circle-section">
          <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-8">Prep circle</h2>
          <div className="space-y-12">
            {circle.map((p) => (
              <div key={p.id}>{renderPerson(p, true)}</div>
            ))}
          </div>
        </motion.section>
      )}

      {rest.length > 0 && (
        <motion.section {...fade}>
          {circle.length > 0 && (
            <h2 className="text-xs tracking-[0.18em] uppercase text-[#8A8F8C] mb-8">Everyone else</h2>
          )}
          <div className="space-y-12">
            {rest.map((p) => (
              <div key={p.id}>{renderPerson(p, false)}</div>
            ))}
          </div>
        </motion.section>
      )}

      {/* Add person */}
      <Modal open={open} onClose={() => setOpen(false)} title="Add a person" testId="person-modal">
        <Field label="Name"><input className={inputClass} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="person-name-input" /></Field>
        <Field label="Relationship"><input className={inputClass} value={form.relation} onChange={(e) => setForm({ ...form, relation: e.target.value })} data-testid="person-relation-input" /></Field>
        <Field label="Company"><input className={inputClass} value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} data-testid="person-company-input" /></Field>
        <Field label="Birthday"><input className={inputClass} value={form.birthday} onChange={(e) => setForm({ ...form, birthday: e.target.value })} data-testid="person-birthday-input" /></Field>
        <Field label="Notes"><textarea className={inputClass} rows={3} value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} data-testid="person-notes-input" /></Field>
        <PrimaryButton onClick={add} data-testid="person-save-btn">Add person</PrimaryButton>
      </Modal>

      {/* Strengths */}
      <Modal open={!!strengthsFor} onClose={() => setStrengthsFor(null)} title={strengthsFor ? `${strengthsFor.name}'s strengths` : ""} testId="strengths-modal">
        <Field label="Strong at">
          <div className="flex flex-wrap gap-2">
            {COMPETENCIES.map((c) => (
              <Chip
                key={c}
                label={c}
                selected={strengthsDraft.strengths.includes(c)}
                onClick={() => toggleStrength(c)}
                testId={`person-strength-chip-${c}`}
              />
            ))}
          </div>
        </Field>
        <Field label="A quiet note (optional)">
          <textarea
            className={inputClass}
            rows={2}
            value={strengthsDraft.note}
            onChange={(e) => setStrengthsDraft({ ...strengthsDraft, note: e.target.value })}
            data-testid="person-strength-note"
          />
        </Field>
        <PrimaryButton onClick={saveStrengths} data-testid="person-strengths-save">Save</PrimaryButton>
      </Modal>

      {/* Log a mock */}
      <Modal open={!!mockFor} onClose={() => setMockFor(null)} title={mockFor ? `A mock with ${mockFor.name}` : ""} testId="mock-modal">
        <Field label="When">
          <input
            type="date"
            className={inputClass}
            value={mockDraft.date}
            onChange={(e) => setMockDraft({ ...mockDraft, date: e.target.value })}
            data-testid="mock-date"
          />
        </Field>
        <Field label="What you practised">
          <div className="flex flex-wrap gap-2">
            {COMPETENCIES.map((c) => (
              <Chip
                key={c}
                label={c}
                selected={mockDraft.competencies.includes(c)}
                onClick={() => toggleMockComp(c)}
                testId={`mock-competency-chip-${c}`}
              />
            ))}
          </div>
        </Field>
        <Field label="For a company (optional)">
          <input className={inputClass} value={mockDraft.company} onChange={(e) => setMockDraft({ ...mockDraft, company: e.target.value })} data-testid="mock-company" />
        </Field>
        <Field label="Feedback">
          <textarea className={inputClass} rows={2} value={mockDraft.feedback} onChange={(e) => setMockDraft({ ...mockDraft, feedback: e.target.value })} data-testid="mock-feedback" />
        </Field>
        <Field label="What went well (optional)">
          <input className={inputClass} value={mockDraft.what_went_well} onChange={(e) => setMockDraft({ ...mockDraft, what_went_well: e.target.value })} data-testid="mock-what-went-well" />
        </Field>
        <Field label="To act on (optional)">
          <input className={inputClass} value={mockDraft.to_act_on} onChange={(e) => setMockDraft({ ...mockDraft, to_act_on: e.target.value })} data-testid="mock-to-act-on" />
        </Field>
        <PrimaryButton onClick={saveMock} data-testid="mock-save">Save</PrimaryButton>
      </Modal>
    </div>
  );
}
