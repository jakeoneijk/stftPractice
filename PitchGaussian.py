import numpy as np
import math
from scipy.interpolate import interp1d
from matplotlib import pyplot as plt

class PitchGaussian():
    def __init__(self,sampling_rate,fft_size,max_frequency_index):
        self.sampling_rate = sampling_rate
        self.fft_size = fft_size
        self.max_frequency_index = max_frequency_index
        self.f0_array = None
        self.is_vocal_array = None
        self.kernel_size = 8 #8
        self.sigma = 25
        self.weight = 1.1
        self.sigma_increase_ration = 1.2
        self.is_vocal_threshold = 0.15
        self.is_vocal_sound_mag = 1.2
        self.is_vocal_range = [int((5500/self.sampling_rate)*(self.max_frequency_index*2)),int((15000/self.sampling_rate)*(self.max_frequency_index*2))] #5500 , 16500
        self.fade_length = 10
        self.fade_in = np.linspace(0,1,self.fade_length)
        self.fade_in = np.tile(self.fade_in,self.max_frequency_index)
        self.fade_in = self.fade_in.reshape(self.max_frequency_index,self.fade_length)
        self.fade_out = np.fliplr(self.fade_in)

    def file_path_to_narray(self,filepath,filepath_isvocal,isRef):
        if isRef == False:
            narray = np.loadtxt(filepath, delimiter=" ")
        else:
            narray = np.loadtxt(filepath, dtype=np.str,delimiter="\t")
        self.f0_array = narray[:,1].astype(float)
        narray = np.loadtxt(filepath_isvocal, delimiter=" ")
        self.is_vocal_array = narray[:,1].astype(float)
        return self.f0_array,self.is_vocal_array

    def hz_to_bin(self,hz):
        return int((hz / self.sampling_rate) * self.fft_size)

    def bin_to_hz(self,bin):
        return (bin / self.fft_size) * self.sampling_rate

    def gaussian_function_array(self,mean,variance,x):
        denominator = math.sqrt(float(2 * math.pi * (variance ** 2)))
        gaussian = np.exp(-1 * (((x - mean) ** 2)/(2 * (variance ** 2)))) / denominator
        max_value = np.max(gaussian)
        return self.weight * (gaussian / max_value)

    def hz_to_gaussian_kernel(self,hz,harmony_index , kernel_size):
        bin_of_hz = self.hz_to_bin(hz)
        start_index = max((bin_of_hz - int(kernel_size / 2)),0)
        end_index = min((bin_of_hz + int(kernel_size / 2)),self.max_frequency_index)

        bin_array = np.arange(start_index , end_index)
        bin_to_hz_array = self.bin_to_hz(bin_array)
        gaussian_value = self.gaussian_function_array(hz,self.sigma * harmony_index,bin_to_hz_array)
        return gaussian_value,start_index,end_index

    def interpolation(self, interpolated_numb):
        if len(self.f0_array) == interpolated_numb:
            return self.f0_array
        old_indices = np.arange(0, len(self.f0_array))
        new_indices = np.linspace(0, len(self.f0_array) - 1, interpolated_numb)
        spl = interp1d(old_indices, self.f0_array, kind='linear')
        new_array = spl(new_indices)
        plt.plot(old_indices,self.f0_array,new_indices, new_array,'r-','b-')
        plt.show()
        return new_array


    def matrix_fit_to_spectro(self,number_time_frame , spec_number):
        self.f0_array = self.f0_array[:number_time_frame]
        #self.f0_array = self.interpolation(spec_number)

        f0_array_transform = np.zeros((self.max_frequency_index, len(self.f0_array)))
        for i in range(0,len(self.f0_array)):
            print(i)
            time_index = int(i)
            masking_hz = self.f0_array[i]
            harmony_index = 1
            while masking_hz < (self.sampling_rate/2) and masking_hz != 0:
                gaussian_array,start_index,end_index = self.hz_to_gaussian_kernel(masking_hz,harmony_index , self.kernel_size * self.sigma_increase_ration)
                f0_array_transform[start_index:end_index,time_index] = f0_array_transform[start_index:end_index,time_index] + gaussian_array
                masking_hz = masking_hz + self.f0_array[i]
                harmony_index = harmony_index * self.sigma_increase_ration
            if self.is_vocal_array[i]>self.is_vocal_threshold and self.f0_array[i] == 0:
                f0_array_transform[self.is_vocal_range[0]:self.is_vocal_range[1], time_index] = self.is_vocal_sound_mag
        return self.fade_in_out(f0_array_transform)
        #return f0_array_transform

    def fade_in_out(self,harmony_arr):
        harmony_array = harmony_arr
        base = np.max(harmony_array,axis=0)
        #base[base<=0.5] = 0
        previous_value_zero = True
        for i in range(len(base)):
            if previous_value_zero:
                if base[i] > 0:
                    fade_index_range = min(len(base)-i,self.fade_length)
                    harmony_array[:,i:i+fade_index_range] = harmony_array[:,i:i+fade_index_range] * self.fade_in[:,0:fade_index_range]
                    previous_value_zero = False
            else :
                if base[i] == 0:
                    fade_index_range = min(i, self.fade_length)
                    harmony_array[:, i-fade_index_range:i] = harmony_array[:, i-fade_index_range:i] * self.fade_out[:,0:fade_index_range]
                    previous_value_zero = True
        return harmony_array

        print("debug")
