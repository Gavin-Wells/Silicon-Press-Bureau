import { useTranslation } from 'react-i18next';
import { Link, useSearchParams } from 'react-router-dom';
import Header from '../components/layout/Header';
import SubmitForm from '../components/submission/SubmitForm';

export default function Submit() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const adMode = searchParams.get('intent') === 'ad';

  return (
    <div className="min-h-screen bg-paper-cream">
      <Header />
      
      <main className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-10 text-center">
          <h1 className="text-4xl font-bold text-ink-dark mb-2">{adMode ? t('submit.adTitle') : t('submit.title')}</h1>
          <div className="divider-ornament">
            <span>{adMode ? '◎' : '✉'}</span>
          </div>
          <p className="text-[#6b5c4d]">
            {adMode ? t('submit.adSubtitle') : t('submit.subtitle')}
          </p>
          <p className="text-sm text-[#9c8b75] mt-2">
            {adMode ? (
              <Link to="/submit" className="hover:underline">{t('submit.switchToNormal')}</Link>
            ) : (
              <Link to="/submit?intent=ad" className="hover:underline">{t('submit.switchToAd')}</Link>
            )}
          </p>
        </div>
        
        <SubmitForm />
      </main>
    </div>
  );
}
