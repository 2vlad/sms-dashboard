import mongoose, { Document, Schema } from 'mongoose';

export interface IMessage extends Document {
  user: mongoose.Types.ObjectId;
  content: string;
  sender: string;
  recipient: string;
  status: 'pending' | 'delivered' | 'failed';
  telegramChatId?: string;
  telegramMessageId?: string;
  twilioMessageId?: string;
  createdAt: Date;
  updatedAt: Date;
}

const MessageSchema = new Schema<IMessage>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
    },
    content: {
      type: String,
      required: true,
    },
    sender: {
      type: String,
      required: true,
    },
    recipient: {
      type: String,
      required: true,
    },
    status: {
      type: String,
      enum: ['pending', 'delivered', 'failed'],
      default: 'pending',
    },
    telegramChatId: {
      type: String,
    },
    telegramMessageId: {
      type: String,
    },
    twilioMessageId: {
      type: String,
    },
  },
  {
    timestamps: true,
  }
);

const Message = mongoose.model<IMessage>('Message', MessageSchema);

export default Message; 