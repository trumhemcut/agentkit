import { Metadata } from 'next';
import { SettingsLayout } from '@/components/Settings/SettingsLayout';

export const metadata: Metadata = {
  title: 'Settings - AgentKit',
  description: 'Configure your agent settings',
};

export default function SettingsPage() {
  return <SettingsLayout />;
}
