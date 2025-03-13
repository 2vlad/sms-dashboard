import mongoose, { Document, Schema } from 'mongoose';

export interface ISetting extends Document {
  user: mongoose.Types.ObjectId;
  forwardAllChats: boolean;
  onlyNonMutedChats: boolean;
  monitoredChats: string[];
  includeSenderName: boolean;
  maxSmsLength: number;
  forwardMedia: boolean;
  forwardOwnMessages: boolean;
  createdAt: Date;
  updatedAt: Date;
}

const SettingSchema = new Schema<ISetting>(
  {
    user: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      unique: true,
    },
    forwardAllChats: {
      type: Boolean,
      default: true,
    },
    onlyNonMutedChats: {
      type: Boolean,
      default: true,
    },
    monitoredChats: {
      type: [String],
      default: [],
    },
    includeSenderName: {
      type: Boolean,
      default: true,
    },
    maxSmsLength: {
      type: Number,
      default: 160,
    },
    forwardMedia: {
      type: Boolean,
      default: true,
    },
    forwardOwnMessages: {
      type: Boolean,
      default: false,
    },
  },
  {
    timestamps: true,
  }
);

const Setting = mongoose.model<ISetting>('Setting', SettingSchema);

export default Setting; 