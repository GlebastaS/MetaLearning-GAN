import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable


class Generator(nn.Module):
    third_stride_dict = {64: 2, 128: 2, 256: 4}
    third_kernel_dict = {64: 4, 128: 4, 256: 6}
    fourth_stride_dict = {64: 2, 128: 4, 256: 4}
    fourth_kernel_dict = {64: 4, 128: 6, 256: 6}

    def __init__(self, data_size: int, meta_length: int, z_length: int):
        super(Generator, self).__init__()

        self.data_size = data_size
        self.meta_length = meta_length
        self.z_length = z_length

        # in (?, z_length, 1, 1)
        # out (?, data_size * 4, 4, 4)
        self.fc_z = nn.ConvTranspose2d(in_channels=self.z_length,
                                       out_channels=self.data_size * 4, kernel_size=4, stride=1, padding=0)
        # in (?, meta_length, 1, 1)
        # out (?, data_size * 4, 4, 4)
        self.fc_meta = nn.ConvTranspose2d(in_channels=self.meta_length,
                                          out_channels=self.data_size * 4, kernel_size=4, stride=1, padding=0)
        # in (?, data_size * 8, 4, 4)
        # out (?, data_size * 4, 8, 8)
        self.deconv1 = nn.ConvTranspose2d(in_channels=self.data_size * 8,
                                          out_channels=self.data_size * 4, kernel_size=4, stride=2, padding=1)
        # out (?, data_size * 2, 16, 16)
        self.deconv2 = nn.ConvTranspose2d(in_channels=self.data_size * 4,
                                          out_channels=self.data_size * 2, kernel_size=4, stride=2, padding=1)
        # out (?, data_size, 32, 32)
        third_kernel = self.third_kernel_dict[data_size]
        third_stride = self.third_stride_dict[data_size]
        self.deconv3 = nn.ConvTranspose2d(in_channels=self.data_size * 2,
                                          out_channels=self.data_size, kernel_size=third_kernel, stride=third_stride,
                                          padding=1)
        # out (?, data_size / 2, 64, 64)
        fourth_kernel = self.fourth_kernel_dict[data_size]
        fourth_stride = self.fourth_stride_dict[data_size]
        self.deconv4 = nn.ConvTranspose2d(in_channels=self.data_size,
                                          out_channels=1, kernel_size=fourth_kernel, stride=fourth_stride, padding=1)

    def forward(self, z, meta):
        fc_z = F.relu(self.fc_z(z))
        fc_meta = F.relu(self.fc_meta(meta))

        fc = torch.cat((fc_z, fc_meta), 1)
        deconv1 = F.relu(self.deconv1(fc))
        deconv2 = F.relu(self.deconv2(deconv1))
        deconv3 = F.relu(self.deconv3(deconv2))
        deconv4 = F.tanh(self.deconv4(deconv3))
        return deconv4


class Discriminator(nn.Module):
    first_stride_dict = {64: 2, 128: 4, 256: 4}
    first_kernel_dict = {64: 4, 128: 6, 256: 6}
    first_size_dict = {64: 32, 128: 64, 256: 64}
    second_stride_dict = {64: 2, 128: 2, 256: 4}
    second_kernel_dict = {64: 4, 128: 4, 256: 6}

    def __init__(self, data_size: int, meta_length: int, lambda_length: int):
        super(Discriminator, self).__init__()

        self.data_size = data_size
        self.meta_length = meta_length
        self.lambda_length = lambda_length

        # in (?, 1, data_size, data_size)
        # out (?, data_size / 2, 32, 32)
        first_kernel = self.first_kernel_dict[data_size]
        first_stride = self.first_stride_dict[data_size]
        self.conv_1 = nn.Conv2d(in_channels=1,
                                out_channels=self.data_size, kernel_size=first_kernel,
                                stride=first_stride,
                                padding=1)
        # in (?, data_size, 32, 32)
        # out (?, data_size * 2, 16, 16)
        second_kernel = self.second_kernel_dict[data_size]
        second_stride = self.second_stride_dict[data_size]
        self.conv_2 = nn.Conv2d(in_channels=self.data_size,
                                out_channels=self.data_size * 2, kernel_size=second_kernel, stride=second_stride,
                                padding=1)
        # out (?, data_size * 4, 8, 8)
        self.conv_3 = nn.Conv2d(in_channels=self.data_size * 2,
                                out_channels=self.data_size * 4, kernel_size=4, stride=2, padding=1)
        # out (?, data_size * 8, 4, 4)
        self.conv_4 = nn.Conv2d(in_channels=self.data_size * 4,
                                out_channels=self.data_size * 8, kernel_size=4, stride=2, padding=1)
        # out (?, self.data_size * 16, 1, 1)
        self.conv_5 = nn.Conv2d(in_channels=self.data_size * 8,
                                out_channels=self.data_size * 16, kernel_size=4, stride=1, padding=0)

        self.fc = nn.Linear(in_features=self.data_size * 16 + self.meta_length, out_features=self.lambda_length + 1)

    def forward(self, data, meta):
        conv1 = F.leaky_relu(self.conv_1(data), 0.2)
        conv2 = F.leaky_relu(self.conv_2(conv1), 0.2)
        conv3 = F.leaky_relu(self.conv_3(conv2), 0.2)
        conv4 = F.leaky_relu(self.conv_4(conv3), 0.2)
        conv5 = F.leaky_relu(self.conv_5(conv4), 0.2)
        concat = torch.cat((conv5, meta), 1)
        result = F.sigmoid(self.fc(concat.squeeze()))
        return result
