import { useState } from 'react';
import { supabase } from '../lib/supabaseClient';

// FR-1.1: email/password or OAuth login via Supabase (JWT-based).
export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    if (error) alert(error.message);
    // TODO: redirect to Dashboard on success
  }

  return (
    <form onSubmit={handleLogin} className="max-w-sm mx-auto mt-20 flex flex-col gap-3">
      <h1 className="text-xl font-bold">Log In</h1>
      <input
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        className="border rounded px-3 py-2"
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        className="border rounded px-3 py-2"
      />
      <button type="submit" className="bg-indigo-600 text-white rounded px-4 py-2">
        Log In
      </button>
    </form>
  );
}
