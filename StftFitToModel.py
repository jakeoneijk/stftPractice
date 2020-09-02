import numpy as np
import librosa
import soundfile as sf
import time

class StftFitToModel():
    def __init__(self):
        self.sampling_rate = 44100
        self.number_fft = 2048
        self.max_frequency_index = int((self.number_fft / 2) + 1)
        self.window_length = 2048 #2048
        self.hop_length = int(self.sampling_rate / 100)
        self.number_time_frame = None
        self.model_input_size = 31
        self.window_type = 'hann'
        

    def down_sampling(self,file_name):
        y, sr = librosa.load(file_name, sr=self.sampling_rate)
        return y

    def down_sampling_and_stft(self,file_name):
        down_sample = self.down_sampling(file_name)
        X = librosa.core.stft(down_sample, n_fft=self.number_fft, hop_length=self.hop_length, win_length=self.window_length , window=self.window_type)
        return X

    def after_processing(self,spectro):
        x_spec = spectro
        num_time_frames = x_spec.shape[1]

        padd_num = self.model_input_size - (num_time_frames % self.model_input_size)

        if padd_num != self.model_input_size:
            padding_feature = np.zeros(shape=(self.max_frequency_index, padd_num))
            x_spec = np.concatenate((x_spec, padding_feature), axis=1)
            num_time_frames = num_time_frames + padd_num

        self.number_time_frame = num_time_frames

        return x_spec
    
    def inverse_stft(self,stft_mat,name):
        iStftMat = librosa.core.istft(stft_mat, hop_length=self.hop_length, window = self.window_type , win_length=self.window_length)
        filename = "./Output/testOut"+ time.strftime('%c', time.localtime(time.time()))+"_"+name+".wav"
        sf.write(filename, iStftMat, self.sampling_rate)
        return iStftMat

    def inverse_stft_griffin_lim(self,stft_mat,name,phaseIterations=10):
        spectrum = stft_mat
        magnitude = abs(stft_mat)
        audio = librosa.istft(spectrum, hop_length=self.hop_length, window = self.window_type , win_length=self.window_length)

        for i in range(phaseIterations):
            filename = "./Output/testOut" + time.strftime('%c', time.localtime(time.time())) + "_" + name + ".wav"
            reconstruction_phase = np.angle(librosa.core.stft(audio, n_fft=self.number_fft, hop_length=self.hop_length, win_length=self.window_length , window=self.window_type))
            spectrum = magnitude * np.exp(1j * reconstruction_phase)
            audio = librosa.istft(spectrum, hop_length=self.hop_length, window = self.window_type , win_length=self.window_length)
        sf.write(filename, audio, self.sampling_rate)


