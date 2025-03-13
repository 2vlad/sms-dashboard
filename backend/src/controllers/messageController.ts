import { Request, Response } from 'express';
import Message from '../models/Message';
import User from '../models/User';
import { Twilio } from 'twilio';

// @desc    Get all messages for a user
// @route   GET /api/messages
// @access  Private
export const getMessages = async (req: Request, res: Response) => {
  try {
    const page = Number(req.query.page) || 1;
    const limit = Number(req.query.limit) || 10;
    const skip = (page - 1) * limit;

    const messages = await Message.find({ user: req.user?._id })
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);

    const total = await Message.countDocuments({ user: req.user?._id });

    res.json({
      messages,
      page,
      pages: Math.ceil(total / limit),
      total,
    });
  } catch (error) {
    console.error('Get messages error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Get message by ID
// @route   GET /api/messages/:id
// @access  Private
export const getMessageById = async (req: Request, res: Response) => {
  try {
    const message = await Message.findOne({
      _id: req.params.id,
      user: req.user?._id,
    });

    if (message) {
      res.json(message);
    } else {
      res.status(404).json({ message: 'Message not found' });
    }
  } catch (error) {
    console.error('Get message by ID error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Send a new SMS message
// @route   POST /api/messages
// @access  Private
export const sendMessage = async (req: Request, res: Response) => {
  try {
    const { content, recipient } = req.body;

    if (!content || !recipient) {
      return res.status(400).json({ message: 'Please provide content and recipient' });
    }

    const user = await User.findById(req.user?._id);

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    if (!user.twilioAccountSid || !user.twilioAuthToken || !user.twilioPhoneNumber) {
      return res.status(400).json({ message: 'Twilio credentials not set up' });
    }

    // Initialize Twilio client
    const twilioClient = new Twilio(user.twilioAccountSid, user.twilioAuthToken);

    // Send SMS via Twilio
    const twilioMessage = await twilioClient.messages.create({
      body: content,
      from: user.twilioPhoneNumber,
      to: recipient,
    });

    // Create message record
    const message = await Message.create({
      user: user._id,
      content,
      sender: user.twilioPhoneNumber,
      recipient,
      status: twilioMessage.status === 'delivered' ? 'delivered' : 'pending',
      twilioMessageId: twilioMessage.sid,
    });

    res.status(201).json(message);
  } catch (error: any) {
    console.error('Send message error:', error);
    
    // Handle Twilio-specific errors
    if (error.code) {
      return res.status(400).json({ 
        message: `Twilio error: ${error.message}`,
        code: error.code,
      });
    }
    
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Get message statistics
// @route   GET /api/messages/stats
// @access  Private
export const getMessageStats = async (req: Request, res: Response) => {
  try {
    // Total messages
    const totalMessages = await Message.countDocuments({ user: req.user?._id });
    
    // Messages by status
    const delivered = await Message.countDocuments({ 
      user: req.user?._id,
      status: 'delivered',
    });
    
    const failed = await Message.countDocuments({ 
      user: req.user?._id,
      status: 'failed',
    });
    
    const pending = await Message.countDocuments({ 
      user: req.user?._id,
      status: 'pending',
    });

    // Messages by date (last 30 days)
    const thirtyDaysAgo = new Date();
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const messagesByDate = await Message.aggregate([
      {
        $match: {
          user: req.user?._id,
          createdAt: { $gte: thirtyDaysAgo },
        },
      },
      {
        $group: {
          _id: { $dateToString: { format: '%Y-%m-%d', date: '$createdAt' } },
          count: { $sum: 1 },
        },
      },
      {
        $sort: { _id: 1 },
      },
    ]);

    res.json({
      totalMessages,
      delivered,
      failed,
      pending,
      deliveryRate: totalMessages > 0 ? (delivered / totalMessages) * 100 : 0,
      messagesByDate,
    });
  } catch (error) {
    console.error('Get message stats error:', error);
    res.status(500).json({ message: 'Server error' });
  }
}; 