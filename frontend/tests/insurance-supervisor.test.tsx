/**
 * Insurance Supervisor UI Tests
 * 
 * Test suite for InsuranceSupervisorIndicator component
 * 
 * This component displays:
 * 1. Supervisor badge when no specialist is selected
 * 2. Supervisor → Specialist badges when a specialist is handling the query
 * 3. Active indicator (pulsing dot) when specialist is actively processing
 * 4. Vietnamese names for specialists (Chuyên gia Chính sách, etc.)
 * 5. Color-coded badges for different specialist types
 */

import { render, screen } from '@testing-library/react';
import { InsuranceSupervisorIndicator } from '@/components/InsuranceSupervisorIndicator';

describe('InsuranceSupervisorIndicator', () => {
  it('renders supervisor badge when no specialist selected', () => {
    render(<InsuranceSupervisorIndicator />);
    expect(screen.getByText('Insurance Supervisor')).toBeInTheDocument();
  });

  it('renders policy specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="policy" />);
    expect(screen.getByText('Chuyên gia Chính sách')).toBeInTheDocument();
    expect(screen.getByText('Supervisor')).toBeInTheDocument();
  });

  it('renders claims specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="claims" />);
    expect(screen.getByText('Chuyên gia Bồi thường')).toBeInTheDocument();
    expect(screen.getByText('Supervisor')).toBeInTheDocument();
  });

  it('renders quoting specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="quoting" />);
    expect(screen.getByText('Chuyên gia Báo giá')).toBeInTheDocument();
    expect(screen.getByText('Supervisor')).toBeInTheDocument();
  });

  it('renders support specialist badge', () => {
    render(<InsuranceSupervisorIndicator specialist="support" />);
    expect(screen.getByText('Hỗ trợ Khách hàng')).toBeInTheDocument();
    expect(screen.getByText('Supervisor')).toBeInTheDocument();
  });

  it('shows active indicator when isActive is true', () => {
    render(<InsuranceSupervisorIndicator specialist="policy" isActive={true} />);
    const indicator = screen.getByRole('status', { name: 'Active indicator' });
    expect(indicator).toBeInTheDocument();
    expect(indicator).toHaveClass('animate-pulse');
  });

  it('does not show active indicator when isActive is false', () => {
    render(<InsuranceSupervisorIndicator specialist="policy" isActive={false} />);
    const indicator = screen.queryByRole('status', { name: 'Active indicator' });
    expect(indicator).not.toBeInTheDocument();
  });

  it('renders routing arrow between supervisor and specialist', () => {
    render(<InsuranceSupervisorIndicator specialist="claims" />);
    expect(screen.getByText('→')).toBeInTheDocument();
  });

  it('does not render routing arrow when no specialist is selected', () => {
    render(<InsuranceSupervisorIndicator />);
    expect(screen.queryByText('→')).not.toBeInTheDocument();
  });

  it('applies correct color classes for policy specialist', () => {
    const { container } = render(<InsuranceSupervisorIndicator specialist="policy" />);
    const badge = container.querySelector('.bg-blue-100');
    expect(badge).toBeInTheDocument();
  });

  it('applies correct color classes for claims specialist', () => {
    const { container } = render(<InsuranceSupervisorIndicator specialist="claims" />);
    const badge = container.querySelector('.bg-green-100');
    expect(badge).toBeInTheDocument();
  });

  it('applies correct color classes for quoting specialist', () => {
    const { container } = render(<InsuranceSupervisorIndicator specialist="quoting" />);
    const badge = container.querySelector('.bg-amber-100');
    expect(badge).toBeInTheDocument();
  });

  it('applies correct color classes for support specialist', () => {
    const { container } = render(<InsuranceSupervisorIndicator specialist="support" />);
    const badge = container.querySelector('.bg-purple-100');
    expect(badge).toBeInTheDocument();
  });
});

