import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { createIncident } from '@/api/endpoints/incidents';
import { IncidentCreate } from '@/types/incidents';
import { Button } from '@/components/ui/Button';
import { ErrorBanner } from '@/components/ui/ErrorBanner';
import { Card } from '@/components/ui/Card';

const initialForm: IncidentCreate = {
  board_id: '',
  batch_id: '',
  line_id: '',
  product_id: '',
  defect_type: '',
  component_designator: '',
  description: '',
};

export function CreateIncidentPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState<IncidentCreate>(initialForm);

  const mutation = useMutation({
    mutationFn: (payload: IncidentCreate) => createIncident(payload),
    onSuccess: (incident) => navigate(`/incidents/${incident.incident_id}`),
  });

  function updateField<K extends keyof IncidentCreate>(key: K, value: IncidentCreate[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  const isDescriptionTooShort = form.description.trim().length === 0;

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (isDescriptionTooShort) return;
    mutation.mutate(form);
  }

  return (
    <div className="max-w-xl">
      <h1 className="mb-4 text-2xl font-bold">New Incident</h1>
      <Card>
        <form onSubmit={handleSubmit} className="space-y-4">
          {mutation.isError && <ErrorBanner error={mutation.error} />}

          {(['board_id', 'batch_id', 'line_id', 'product_id', 'defect_type'] as const).map((field) => (
            <div key={field}>
              <label htmlFor={field} className="mb-1 block text-sm font-medium capitalize">
                {field.replace(/_/g, ' ')}
              </label>
              <input
                id={field}
                required
                className="w-full rounded-md border border-slate-300 px-3 py-2"
                value={form[field]}
                onChange={(e) => updateField(field, e.target.value)}
              />
            </div>
          ))}

          <div>
            <label htmlFor="component_designator" className="mb-1 block text-sm font-medium">
              Component Designator (optional)
            </label>
            <input
              id="component_designator"
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={form.component_designator ?? ''}
              onChange={(e) => updateField('component_designator', e.target.value)}
            />
          </div>

          <div>
            <label htmlFor="description" className="mb-1 block text-sm font-medium">
              Description
            </label>
            <textarea
              id="description"
              required
              rows={4}
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={form.description}
              onChange={(e) => updateField('description', e.target.value)}
            />
          </div>

          <Button type="submit" isLoading={mutation.isPending} disabled={isDescriptionTooShort}>
            Create Incident
          </Button>
        </form>
      </Card>
    </div>
  );
}