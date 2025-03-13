import { Request, Response } from 'express';
import Setting from '../models/Setting';

// @desc    Get user settings
// @route   GET /api/settings
// @access  Private
export const getSettings = async (req: Request, res: Response) => {
  try {
    let settings = await Setting.findOne({ user: req.user?._id });

    // If settings don't exist, create default settings
    if (!settings) {
      settings = await Setting.create({
        user: req.user?._id,
      });
    }

    res.json(settings);
  } catch (error) {
    console.error('Get settings error:', error);
    res.status(500).json({ message: 'Server error' });
  }
};

// @desc    Update user settings
// @route   PUT /api/settings
// @access  Private
export const updateSettings = async (req: Request, res: Response) => {
  try {
    const {
      forwardAllChats,
      onlyNonMutedChats,
      monitoredChats,
      includeSenderName,
      maxSmsLength,
      forwardMedia,
      forwardOwnMessages,
    } = req.body;

    let settings = await Setting.findOne({ user: req.user?._id });

    if (!settings) {
      // If settings don't exist, create new settings
      settings = await Setting.create({
        user: req.user?._id,
        ...(forwardAllChats !== undefined && { forwardAllChats }),
        ...(onlyNonMutedChats !== undefined && { onlyNonMutedChats }),
        ...(monitoredChats !== undefined && { monitoredChats }),
        ...(includeSenderName !== undefined && { includeSenderName }),
        ...(maxSmsLength !== undefined && { maxSmsLength }),
        ...(forwardMedia !== undefined && { forwardMedia }),
        ...(forwardOwnMessages !== undefined && { forwardOwnMessages }),
      });
    } else {
      // Update existing settings
      if (forwardAllChats !== undefined) settings.forwardAllChats = forwardAllChats;
      if (onlyNonMutedChats !== undefined) settings.onlyNonMutedChats = onlyNonMutedChats;
      if (monitoredChats !== undefined) settings.monitoredChats = monitoredChats;
      if (includeSenderName !== undefined) settings.includeSenderName = includeSenderName;
      if (maxSmsLength !== undefined) settings.maxSmsLength = maxSmsLength;
      if (forwardMedia !== undefined) settings.forwardMedia = forwardMedia;
      if (forwardOwnMessages !== undefined) settings.forwardOwnMessages = forwardOwnMessages;

      await settings.save();
    }

    res.json(settings);
  } catch (error) {
    console.error('Update settings error:', error);
    res.status(500).json({ message: 'Server error' });
  }
}; 