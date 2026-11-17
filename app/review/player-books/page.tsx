import PlayerBookReview from './review';
import {BOOK_EXPERIENCE_ENABLED} from '../../components/shelfState';
import {notFound} from 'next/navigation';

export const metadata = { title: 'Player & book review — Brian Zeng', robots: { index: false, follow: false } };
export default function ReviewPage() { if(!BOOK_EXPERIENCE_ENABLED) notFound(); return <PlayerBookReview />; }
