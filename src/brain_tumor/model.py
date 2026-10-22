import torch
from torch import nn


class Block(nn.Module):
    def __init__(self, input_channels, output_channels):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(input_channels, output_channels, 3, padding=1),
            nn.GroupNorm(4, output_channels), nn.ReLU(inplace=True),
            nn.Conv2d(output_channels, output_channels, 3, padding=1),
            nn.GroupNorm(4, output_channels), nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.net(x)


class UNet(nn.Module):
    def __init__(self, base=16):
        super().__init__()
        self.down1 = Block(1, base)
        self.down2 = Block(base, base*2)
        self.down3 = Block(base*2, base*4)
        self.bridge = Block(base*4, base*8)
        self.pool = nn.MaxPool2d(2)
        self.up3 = nn.ConvTranspose2d(base*8, base*4, 2, stride=2)
        self.dec3 = Block(base*8, base*4)
        self.up2 = nn.ConvTranspose2d(base*4, base*2, 2, stride=2)
        self.dec2 = Block(base*4, base*2)
        self.up1 = nn.ConvTranspose2d(base*2, base, 2, stride=2)
        self.dec1 = Block(base*2, base)
        self.out = nn.Conv2d(base, 1, 1)

    def forward(self, x):
        a = self.down1(x)
        b = self.down2(self.pool(a))
        c = self.down3(self.pool(b))
        d = self.bridge(self.pool(c))
        c = self.dec3(torch.cat((self.up3(d), c), dim=1))
        b = self.dec2(torch.cat((self.up2(c), b), dim=1))
        a = self.dec1(torch.cat((self.up1(b), a), dim=1))
        return self.out(a)


def loss_fn(logits, target):
    bce = nn.functional.binary_cross_entropy_with_logits(logits, target)
    prob = logits.sigmoid()
    dims = (1, 2, 3)
    dice = (2 * (prob * target).sum(dims) + 1) / (prob.sum(dims) + target.sum(dims) + 1)
    return bce + (1 - dice.mean())
