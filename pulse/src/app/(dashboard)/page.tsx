import { Metadata } from 'next';
import DashboardClient from './page.client';

export const metadata: Metadata = {
  title: 'Boss Dashboard | DS',
};

export default async function DashboardPage() {
  return <DashboardClient />;
}
