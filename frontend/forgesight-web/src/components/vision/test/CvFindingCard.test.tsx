import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { CvFindingCard } from '../CvFindingCard';

describe('CvFindingCard', () => {
  it('always renders the dataset_used_for_training disclosure (Mandatory Rule 7)', () => {
    render(
      <CvFindingCard
        defectType="component_misalignment"
        componentDesignator="C17"
        confidence={0.91}
        modelVersion="synthetic-v1"
        datasetUsedForTraining="synthetic-placeholder-v1 (not for production use)"
      />
    );

    const disclosure = screen.getByTestId('dataset-disclosure');
    expect(disclosure).toHaveTextContent('synthetic-placeholder-v1 (not for production use)');
  });

  it('renders defect type and confidence', () => {
    render(
      <CvFindingCard
        defectType="tombstoning"
        componentDesignator={null}
        confidence={0.75}
        modelVersion="v2"
        datasetUsedForTraining="real-dataset-v2"
      />
    );
    expect(screen.getByText(/tombstoning/)).toBeInTheDocument();
    expect(screen.getByText(/75% confidence/)).toBeInTheDocument();
  });
});