import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Hero } from '../Hero';

describe('Hero Component', () => {
  it('renders headline, url input, and analyze button', () => {
    const handleUrlChange = vi.fn();
    const handleAnalyze = vi.fn();

    render(
      <Hero
        url=""
        onUrlChange={handleUrlChange}
        onAnalyze={handleAnalyze}
        isLoading={false}
      />
    );

    expect(screen.getByText(/Your videos\. Your quality\./i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Paste video URL/i)).toBeInTheDocument();
    const button = screen.getByRole('button', { name: /Analyze Video/i });
    expect(button).toBeInTheDocument();
    expect(button).toBeDisabled();
  });

  it('triggers analyze when Enter key is pressed', () => {
    const handleUrlChange = vi.fn();
    const handleAnalyze = vi.fn();

    render(
      <Hero
        url="https://test-media.local/watch?v=sample"
        onUrlChange={handleUrlChange}
        onAnalyze={handleAnalyze}
        isLoading={false}
      />
    );

    const input = screen.getByPlaceholderText(/Paste video URL/i);
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    expect(handleAnalyze).toHaveBeenCalledTimes(1);
  });

  it('displays validation error message when provided', () => {
    render(
      <Hero
        url="http://invalid-url"
        onUrlChange={vi.fn()}
        onAnalyze={vi.fn()}
        isLoading={false}
        errorMessage="Domain is not authorized."
      />
    );

    expect(screen.getByText(/URL Validation Notice/i)).toBeInTheDocument();
    expect(screen.getByText(/Domain is not authorized\./i)).toBeInTheDocument();
  });
});
