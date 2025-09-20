'use client';

import { useAuth } from '../../../context/AuthContext';

export default function RenterDashboard() {
  const { user } = useAuth();

  if (!user) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h1>Renter Dashboard</h1>
      <p>Welcome, {user.sub}!</p>
      {/* Contract View, Payment History, and Payment Upload components will go here */}
    </div>
  );
}
