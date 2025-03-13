import express from 'express';
import { 
  getMessages, 
  getMessageById, 
  sendMessage, 
  getMessageStats 
} from '../controllers/messageController';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// All routes are protected
router.use(authenticate);

router.route('/')
  .get(getMessages)
  .post(sendMessage);

router.get('/stats', getMessageStats);
router.get('/:id', getMessageById);

export default router; 