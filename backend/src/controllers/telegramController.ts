import { Request, Response } from 'express';
import { Telegraf } from 'telegraf';
import User from '../models/User';

// Initialize Telegram bot
const bot = new Telegraf(process.env.TELEGRAM_BOT_TOKEN || '');

// @desc    Start Telegram authentication process
// @route   POST /api/telegram/auth/start
// @access  Private
export const startTelegramAuth = async (req: Request, res: Response) => {
  try {
    const { phoneNumber } = req.body;

    if (!phoneNumber) {
      return res.status(400).json({ message: 'Phone number is required' });
    }

    // In a real implementation, you would use the Telegram Client API (MTProto)
    // to send a verification code to the user's phone number
    // This is a simplified version for demonstration purposes

    // Generate a random verification code
    const verificationCode = Math.floor(100000 + Math.random() * 900000).toString();

    // Store the verification code in the user's record
    const user = await User.findById(req.user?._id);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    user.telegramPhoneNumber = phoneNumber;
    // In a real implementation, you would store this securely
    // This is just for demonstration
    user.telegramSessionString = verificationCode;
    await user.save();

    // In a real implementation, Telegram would send the code
    // For demo purposes, we'll just return it
    res.json({
      message: 'Verification code sent to your phone',
      // In production, you would NOT send this back to the client
      // This is just for demonstration
      verificationCode,
    });
  } catch (error) {
    console.error('Start Telegram auth error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Verify Telegram authentication code
// @route   POST /api/telegram/auth/verify
// @access  Private
export const verifyTelegramCode = async (req: Request, res: Response) => {
  try {
    const { verificationCode } = req.body;

    if (!verificationCode) {
      return res.status(400).json({ message: 'Verification code is required' });
    }

    // Find the user
    const user = await User.findById(req.user?._id);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Check if the verification code matches
    // In a real implementation, you would use the Telegram Client API
    // to verify the code and get the user's Telegram ID
    if (user.telegramSessionString !== verificationCode) {
      return res.status(400).json({ message: 'Invalid verification code' });
    }

    // In a real implementation, you would get these from the Telegram API
    // This is just for demonstration
    const telegramId = `telegram_${Math.floor(Math.random() * 1000000000)}`;
    const telegramUsername = `user_${Math.floor(Math.random() * 1000000)}`;

    // Update user with Telegram information
    user.telegramId = telegramId;
    user.telegramUsername = telegramUsername;
    // Clear the verification code
    user.telegramSessionString = '';
    await user.save();

    res.json({
      message: 'Telegram authentication successful',
      telegramId,
      telegramUsername,
    });
  } catch (error) {
    console.error('Verify Telegram code error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Disconnect Telegram account
// @route   POST /api/telegram/disconnect
// @access  Private
export const disconnectTelegram = async (req: Request, res: Response) => {
  try {
    const user = await User.findById(req.user?._id);
    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Clear Telegram information
    user.telegramId = undefined;
    user.telegramUsername = undefined;
    user.telegramPhoneNumber = undefined;
    user.telegramSessionString = '';
    await user.save();

    res.json({ message: 'Telegram account disconnected successfully' });
  } catch (error) {
    console.error('Disconnect Telegram error:', error);
    res.status(500).json({ message: 'Server error' });
  }
}; 