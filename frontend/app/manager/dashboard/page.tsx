'use client';

import { useAuth } from '../../../context/AuthContext';

export default function ManagerDashboard() {
  const { user } = useAuth();

  if (!user) {
    return <div>Loading...</div>;
  }

  // A simple redirect could be done here if user is not a manager
  // but for now we assume routing logic gets them here correctly.

  return (
    <div>
      <h1>Manager Dashboard</h1>
      <p>Welcome, {user.sub}!</p>
      <p>Your role is: {user.role}</p>
      <p>Your realm is: {user.realm}</p>
      {/* Room Management, Renter Management, and Payment Approval components will go here */}
    </div>
  );
}
