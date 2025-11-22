import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('renders the main heading', () => {
    render(<App />);
    const heading = screen.getByText(/Video Downloader/i);
    expect(heading).toBeDefined();
  });

  it('renders the URL input field', () => {
    render(<App />);
    const input = screen.getByPlaceholderText(/Enter webpage URL/i);
    expect(input).toBeDefined();
  });

  it('renders the extract button', () => {
    render(<App />);
    const button = screen.getByText(/Extract Video/i);
    expect(button).toBeDefined();
  });

  it('renders the legal notice', () => {
    render(<App />);
    const notice = screen.getByText(/Legal Notice/i);
    expect(notice).toBeDefined();
  });

  it('has HLS conversion checkbox', () => {
    render(<App />);
    const checkbox = screen.getByLabelText(/Convert HLS/i);
    expect(checkbox).toBeDefined();
  });
});
