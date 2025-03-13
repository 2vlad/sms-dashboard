import express from 'express';
import { getSettings, updateSettings } from '../controllers/settingController';
import { authenticate } from '../middleware/auth';

const router = express.Router();

// All routes are protected
router.use(authenticate);

router.route('/')
  .get(getSettings)
  .put(updateSettings);

export default router; 