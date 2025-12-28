/**
 * A2UIBarChart Component Tests
 * 
 * Test suite for A2UIBarChart component that renders bar charts
 * following the A2UI protocol specification.
 * 
 * Tests cover:
 * 1. Chart rendering with valid data
 * 2. Multiple data series support
 * 3. Custom colors
 * 4. Empty data handling
 * 5. Data model path resolution
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { A2UIBarChart } from '@/components/A2UI/components/A2UIBarChart';

describe('A2UIBarChart', () => {
  const mockDataModel = {
    ui: {
      'chart-123': {
        chartData: {
          data: [
            { category: 'Jan', desktop: 186, mobile: 80 },
            { category: 'Feb', desktop: 305, mobile: 200 },
            { category: 'Mar', desktop: 237, mobile: 120 },
          ],
          dataKeys: ['desktop', 'mobile'],
        },
      },
    },
  };

  it('renders chart with title', () => {
    render(
      <A2UIBarChart
        id="chart-123"
        props={{
          title: { literalString: 'User Statistics' },
          dataKeys: { literalString: 'desktop,mobile' },
          data: { path: '/ui/chart-123/chartData' },
        }}
        dataModel={mockDataModel}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('User Statistics')).toBeInTheDocument();
  });

  it('renders chart with title and description', () => {
    render(
      <A2UIBarChart
        id="chart-123"
        props={{
          title: { literalString: 'User Statistics' },
          description: { literalString: 'Monthly active users' },
          dataKeys: { literalString: 'desktop,mobile' },
          data: { path: '/ui/chart-123/chartData' },
        }}
        dataModel={mockDataModel}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('User Statistics')).toBeInTheDocument();
    expect(screen.getByText('Monthly active users')).toBeInTheDocument();
  });

  it('shows no data message when data is empty', () => {
    render(
      <A2UIBarChart
        id="chart-456"
        props={{
          title: { literalString: 'Empty Chart' },
          dataKeys: { literalString: 'desktop' },
          data: { path: '/invalid/path' },
        }}
        dataModel={{}}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Empty Chart')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('shows no data message when path does not exist in data model', () => {
    render(
      <A2UIBarChart
        id="chart-789"
        props={{
          title: { literalString: 'Missing Data Chart' },
          dataKeys: { literalString: 'value' },
          data: { path: '/nonexistent/path' },
        }}
        dataModel={mockDataModel}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Missing Data Chart')).toBeInTheDocument();
    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('renders chart with custom colors', () => {
    const { container } = render(
      <A2UIBarChart
        id="chart-123"
        props={{
          title: { literalString: 'Sales Data' },
          dataKeys: { literalString: 'revenue,profit' },
          colors: {
            literalMap: {
              revenue: '#10b981',
              profit: '#3b82f6',
            },
          },
          data: { path: '/ui/chart-123/chartData' },
        }}
        dataModel={{
          ui: {
            'chart-123': {
              chartData: {
                data: [
                  { category: 'Q1', revenue: 50000, profit: 15000 },
                  { category: 'Q2', revenue: 60000, profit: 18000 },
                ],
              },
            },
          },
        }}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Sales Data')).toBeInTheDocument();
    // Chart container should be rendered (chart itself renders with zero size in tests)
    expect(container.querySelector('[data-chart]')).toBeInTheDocument();
  });

  it('handles single data series', () => {
    render(
      <A2UIBarChart
        id="chart-single"
        props={{
          title: { literalString: 'Single Series Chart' },
          dataKeys: { literalString: 'value' },
          data: { path: '/ui/chart-single/chartData' },
        }}
        dataModel={{
          ui: {
            'chart-single': {
              chartData: {
                data: [
                  { category: 'A', value: 100 },
                  { category: 'B', value: 200 },
                  { category: 'C', value: 150 },
                ],
              },
            },
          },
        }}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Single Series Chart')).toBeInTheDocument();
  });

  it('handles multiple data series', () => {
    const { container } = render(
      <A2UIBarChart
        id="chart-multi"
        props={{
          title: { literalString: 'Multi Series Chart' },
          dataKeys: { literalString: 'desktop,mobile,tablet' },
          data: { path: '/ui/chart-multi/chartData' },
        }}
        dataModel={{
          ui: {
            'chart-multi': {
              chartData: {
                data: [
                  { category: 'Jan', desktop: 186, mobile: 80, tablet: 45 },
                  { category: 'Feb', desktop: 305, mobile: 200, tablet: 120 },
                ],
              },
            },
          },
        }}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Multi Series Chart')).toBeInTheDocument();
    // Chart container should be rendered with multiple series
    expect(container.querySelector('[data-chart]')).toBeInTheDocument();
  });

  it('handles empty dataKeys string gracefully', () => {
    render(
      <A2UIBarChart
        id="chart-empty-keys"
        props={{
          title: { literalString: 'Empty Keys Chart' },
          dataKeys: { literalString: '' },
          data: { path: '/ui/chart-123/chartData' },
        }}
        dataModel={mockDataModel}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Empty Keys Chart')).toBeInTheDocument();
  });

  it('renders with default title when title is missing', () => {
    render(
      <A2UIBarChart
        id="chart-no-title"
        props={{
          title: { literalString: '' },
          dataKeys: { literalString: 'desktop,mobile' },
          data: { path: '/ui/chart-123/chartData' },
        }}
        dataModel={mockDataModel}
        surfaceId="surface-1"
      />
    );

    // Component should still render with chart data from mockDataModel
    // Even though title is empty, the chart should render if data is available
    expect(screen.getByText('Chart')).toBeInTheDocument(); // Default title
  });

  it('handles deeply nested data paths', () => {
    const { container } = render(
      <A2UIBarChart
        id="chart-nested"
        props={{
          title: { literalString: 'Nested Data Chart' },
          dataKeys: { literalString: 'value' },
          data: { path: '/level1/level2/level3/chartData' },
        }}
        dataModel={{
          level1: {
            level2: {
              level3: {
                chartData: {
                  data: [
                    { category: 'A', value: 100 },
                    { category: 'B', value: 200 },
                  ],
                },
              },
            },
          },
        }}
        surfaceId="surface-1"
      />
    );

    expect(screen.getByText('Nested Data Chart')).toBeInTheDocument();
    // Chart container should be rendered with nested data
    expect(container.querySelector('[data-chart]')).toBeInTheDocument();
  });
});
