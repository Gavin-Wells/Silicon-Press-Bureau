import { useTranslation } from 'react-i18next';
import Header from '../components/layout/Header';
import RejectionWall from '../components/rejection/RejectionWall';

export default function Rejections() {
  const { t } = useTranslation();
  return (
    <div className="min-h-screen bg-paper-cream">
      <Header />
      <main className="max-w-5xl mx-auto px-6 py-12">
        <div className="mb-12 text-center">
          <div className="inline-block relative">
            <div className="absolute -top-2 -left-2 w-4 h-4 rounded-full bg-[#8b4513] shadow-md"></div>
            <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-[#8b4513] shadow-md"></div>
            <div className="bg-paper-aged border-2 border-ink-dark p-6 min-w-[300px]">
              <h1 className="text-3xl font-bold text-ink-dark mb-2 flex items-center justify-center space-x-3">
                <span>📌</span>
                <span>{t('rejections.title')}</span>
              </h1>
              <p className="text-[#6b5c4d] font-serif italic">
                "{t('rejections.tagline')}"
              </p>
            </div>
          </div>
          <div className="mt-6 flex items-center justify-center space-x-2 text-sm font-mono text-[#9c8b75]">
            <span className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></span>
            <span>{t('rejections.dailyUpdate')}</span>
          </div>
        </div>
        <RejectionWall />
      </main>
    </div>
  );
}
