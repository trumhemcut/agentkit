'use client';

import React, { useMemo } from 'react';
import { Bar, BarChart, CartesianGrid, XAxis } from 'recharts';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  ChartLegend,
  ChartLegendContent,
  type ChartConfig,
} from '@/components/ui/chart';
import type { A2UIDataModel } from '@/types/a2ui';

interface A2UIBarChartProps {
  id: string;
  props: {
    title: { literalString: string };
    description?: { literalString: string };
    dataKeys: { literalString: string }; // comma-separated: "desktop,mobile"
    colors?: { literalMap: Record<string, string> };
    data: { path: string };
  };
  dataModel: A2UIDataModel;
  surfaceId: string;
}

export const A2UIBarChart: React.FC<A2UIBarChartProps> = ({
  id,
  props,
  dataModel,
  surfaceId,
}) => {
  // Extract props
  const title = props.title?.literalString || 'Chart';
  const description = props.description?.literalString || '';
  const dataKeysString = props.dataKeys?.literalString || '';
  const dataKeys = dataKeysString.split(',').filter(Boolean);
  const colors = props.colors?.literalMap || {};
  const dataPath = props.data?.path || '';

  // Get chart data from data model
  const chartData = useMemo(() => {
    if (!dataPath || !dataModel) return [];
    
    // Navigate data model path
    const pathParts = dataPath.split('/').filter(Boolean);
    let current: any = dataModel;
    
    for (const part of pathParts) {
      current = current?.[part];
    }
    
    return current?.data || [];
  }, [dataPath, dataModel]);

  // Build chart config from data keys and colors
  const chartConfig = useMemo(() => {
    const config: ChartConfig = {};
    
    dataKeys.forEach((key) => {
      config[key] = {
        label: key.charAt(0).toUpperCase() + key.slice(1),
        color: colors[key] || `hsl(var(--chart-${dataKeys.indexOf(key) + 1}))`,
      };
    });
    
    return config;
  }, [dataKeys, colors]);

  if (!chartData || chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-sm">No data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="min-h-[200px] w-full">
          <BarChart accessibilityLayer data={chartData}>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="category"
              tickLine={false}
              tickMargin={10}
              axisLine={false}
              tickFormatter={(value) => {
                // Truncate long labels
                return value.length > 10 ? value.slice(0, 10) + '...' : value;
              }}
            />
            <ChartTooltip content={<ChartTooltipContent />} />
            <ChartLegend content={<ChartLegendContent />} />
            {dataKeys.map((key) => (
              <Bar
                key={key}
                dataKey={key}
                fill={`var(--color-${key})`}
                radius={4}
              />
            ))}
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
};
