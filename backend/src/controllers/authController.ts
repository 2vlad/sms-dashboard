import { Request, Response } from 'express';
import jwt from 'jsonwebtoken';
import User, { IUser } from '../models/User';
import Setting from '../models/Setting';

// Generate JWT token
const generateToken = (id: string): string => {
  return jwt.sign({ id }, process.env.JWT_SECRET || 'fallback_secret', {
    expiresIn: process.env.JWT_EXPIRES_IN || '7d',
  });
};

// @desc    Register a new user
// @route   POST /api/auth/register
// @access  Public
export const register = async (req: Request, res: Response) => {
  try {
    const { email, password, name } = req.body;

    // Check if user already exists
    const userExists = await User.findOne({ email });
    if (userExists) {
      return res.status(400).json({ message: 'User already exists' });
    }

    // Create new user
    const user = await User.create({
      email,
      password,
      name,
    });

    // Create default settings for the user
    await Setting.create({
      user: user._id,
    });

    if (user) {
      res.status(201).json({
        _id: user._id,
        name: user.name,
        email: user.email,
        token: generateToken(user._id.toString()),
      });
    } else {
      res.status(400).json({ message: 'Invalid user data' });
    }
  } catch (error) {
    console.error('Register error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Login user & get token
// @route   POST /api/auth/login
// @access  Public
export const login = async (req: Request, res: Response) => {
  try {
    const { email, password } = req.body;

    // Find user by email
    const user = await User.findOne({ email });

    // Check if user exists and password is correct
    if (user && (await user.comparePassword(password))) {
      res.json({
        _id: user._id,
        name: user.name,
        email: user.email,
        telegramId: user.telegramId,
        telegramUsername: user.telegramUsername,
        telegramPhoneNumber: user.telegramPhoneNumber,
        twilioAccountSid: user.twilioAccountSid ? true : false,
        twilioAuthToken: user.twilioAuthToken ? true : false,
        twilioPhoneNumber: user.twilioPhoneNumber,
        targetPhoneNumber: user.targetPhoneNumber,
        token: generateToken(user._id.toString()),
      });
    } else {
      res.status(401).json({ message: 'Invalid email or password' });
    }
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Get user profile
// @route   GET /api/auth/profile
// @access  Private
export const getProfile = async (req: Request, res: Response) => {
  try {
    const user = await User.findById(req.user?._id).select('-password');
    if (user) {
      res.json({
        _id: user._id,
        name: user.name,
        email: user.email,
        telegramId: user.telegramId,
        telegramUsername: user.telegramUsername,
        telegramPhoneNumber: user.telegramPhoneNumber,
        twilioAccountSid: user.twilioAccountSid ? true : false,
        twilioAuthToken: user.twilioAuthToken ? true : false,
        twilioPhoneNumber: user.twilioPhoneNumber,
        targetPhoneNumber: user.targetPhoneNumber,
      });
    } else {
      res.status(404).json({ message: 'User not found' });
    }
  } catch (error) {
    console.error('Get profile error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Update user profile
// @route   PUT /api/auth/profile
// @access  Private
export const updateProfile = async (req: Request, res: Response) => {
  try {
    const user = await User.findById(req.user?._id);

    if (user) {
      user.name = req.body.name || user.name;
      user.email = req.body.email || user.email;
      
      if (req.body.password) {
        user.password = req.body.password;
      }

      // Update Twilio credentials
      if (req.body.twilioAccountSid) {
        user.twilioAccountSid = req.body.twilioAccountSid;
      }
      
      if (req.body.twilioAuthToken) {
        user.twilioAuthToken = req.body.twilioAuthToken;
      }
      
      if (req.body.twilioPhoneNumber) {
        user.twilioPhoneNumber = req.body.twilioPhoneNumber;
      }
      
      if (req.body.targetPhoneNumber) {
        user.targetPhoneNumber = req.body.targetPhoneNumber;
      }

      const updatedUser = await user.save();

      res.json({
        _id: updatedUser._id,
        name: updatedUser.name,
        email: updatedUser.email,
        telegramId: updatedUser.telegramId,
        telegramUsername: updatedUser.telegramUsername,
        telegramPhoneNumber: updatedUser.telegramPhoneNumber,
        twilioAccountSid: updatedUser.twilioAccountSid ? true : false,
        twilioAuthToken: updatedUser.twilioAuthToken ? true : false,
        twilioPhoneNumber: updatedUser.twilioPhoneNumber,
        targetPhoneNumber: updatedUser.targetPhoneNumber,
        token: generateToken(updatedUser._id.toString()),
      });
    } else {
      res.status(404).json({ message: 'User not found' });
    }
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ message: 'Server error' });
  }
}; 