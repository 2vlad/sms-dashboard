import express from 'express';
import { 
  startTelegramAuth, 
  verifyTelegramCode, 
  disconnectTelegram 
} from '../controllers/telegramController';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// All routes are protected
router.use(authenticate);

// Telegram authentication routes
router.post('/auth/start', startTelegramAuth);
router.post('/auth/verify', verifyTelegramCode);

// Disconnect Telegram account
router.post('/disconnect', disconnectTelegram);

export default router; 