import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import Header from '../components/layout/Header';
import { api } from '../services/api';
import { setAuthUser } from '../lib/auth';

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [penName, setPenName] = useState('');
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const canSubmit = username.trim().length >= 2 && password.length >= 4 && !loading;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError('');
    try {
      const { user, access_token } = await api.login({
        username: username.trim(),
        password: password,
        pen_name: penName.trim() || undefined,
        email: email.trim() || undefined,
      });
      setAuthUser(
        { id: user.id, username: user.username, pen_name: user.pen_name, email: user.email },
        access_token,
      );
      navigate('/my-submissions');
    } catch (err: any) {
      setError(err.message || t('login.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-paper-cream">
      <Header />
      <main className="max-w-2xl mx-auto px-6 py-12">
        <div className="paper-texture border-2 border-ink-dark p-8">
          <h1 className="text-3xl font-bold text-ink-dark mb-2">{t('login.title')}</h1>
          <p className="text-[#6b5c4d] mb-6">
            {t('login.subtitle')}
          </p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-ink-dark mb-2">{t('login.usernameLabel')}</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-vintage"
                placeholder={t('login.usernamePlaceholder')}
                minLength={2}
                maxLength={50}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-dark mb-2">{t('login.passwordLabel')}</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-vintage"
                placeholder={t('login.passwordPlaceholder')}
                minLength={4}
                maxLength={64}
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-dark mb-2">{t('login.penNameLabel')}</label>
              <input
                type="text"
                value={penName}
                onChange={(e) => setPenName(e.target.value)}
                className="input-vintage"
                placeholder={t('submitForm.penNamePlaceholder')}
                maxLength={50}
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-ink-dark mb-2">{t('login.emailLabel')}</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="input-vintage"
                placeholder={t('login.emailPlaceholder')}
                maxLength={100}
              />
            </div>

            {error && <div className="p-3 rounded bg-red-50 border border-red-200 text-sm text-red-700">{error}</div>}

            <button
              type="submit"
              disabled={!canSubmit}
              className="btn-vintage w-full py-3 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? t('login.submitting') : t('login.submit')}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
