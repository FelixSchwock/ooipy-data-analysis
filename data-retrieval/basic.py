"""
Module for hydrophone (acoustic) data objects

The HydrophoneData objects inherits from obspy.Trace. Furthermore,
methods for computing spectrograms and power spectral densities are
added.
"""
import numpy as np
import json
from matplotlib import pyplot as plt
from obspy import Trace
from obspy.core import UTCDateTime
from scipy import signal
from scipy.interpolate import interp1d
import matplotlib.dates as mdates
import matplotlib.colors as colors
import matplotlib
import datetime
import multiprocessing as mp
import pickle
from scipy.io import wavfile
import warnings
import ooipy


class HydrophoneData(Trace):
    """
    Object that stores hydrophone data

    Attributes
    ----------
    spectrogram : Spectrogram
        spectrogram of HydrophoneData.data.data.
        Spectral level, time, and frequency bins can be accessed by
        spectrogram.values, spectrogram.time, and spectrogram.freq
    psd : Psd
        power spectral density estimate of HydrophoneData.data.data.
        Spectral level and frequency bins can be accessed by
        psd.values and psd.freq
    psd_list : list of :class:`.Psd`
        the data object is divided into N segments and for each
        segment a separate power spectral density estimate is computed and
        stored in psd_list. psd_list is computed by compute_psd_welch_mp

    """

    def __init__(self, data=np.array([]), header=None, node=''):

        super().__init__(data, header)
        self.stats.location = node

        self.spectrogram = None
        self.psd = None
        self.psd_list = None

    # TODO: use correct frequency response for all hydrophones
    def freq_dependent_sensitivity_correct(self, N, node, time):
        # TODO
        """
        Apply a frequency dependent sensitivity correction to the
        acoustic data based on the information from the calibration
        sheets.
        TODO Add for all broadband hydrophones
        !!! Currently only implemented for Oregon Offshore Base Seafloor
        and Oregon Shelf Base Seafloor hydrophone. For all other
        hydrophones, an average sensitivity of -169dBV/1uPa is assumed
        !!!

        Parameters
        ----------
        N : int
            length of the data segment
        node : str
            hydrophone node
        time : datetime.datetime
            time of acoustic data. The sensitivity correction varies
            depending on the measurement time

        Returns
        -------
        output_array : np.array
            array with correction coefficient for every frequency
        """

        f = np.linspace(0, 32000, N)
        if node == '/LJ01C':  # Oregon Offshore Base Seafloor
            if time >= datetime.datetime(2014, 8, 15, 0, 12, 0) and \
                    time <= datetime.datetime(2015, 8, 2, 0, 0, 0) or \
                    time >= datetime.datetime(2016, 7, 22, 22, 50, 0) and \
                    time <= datetime.datetime(2017, 8, 10, 4, 0, 0):  # 1249
                f_calib = [0, 26, 13500, 27100, 40600, 54100]
                sens_calib = [168.49, 168.49, 169.3, 169.6, 172.6, 171.8]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2020, 9, 1, 0, 0, 0):  # 1249
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [168.5, 168.5, 167.6, 169.45, 171.85,
                              172.65, 171.7]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2018, 6, 25, 0, 0, 0) and \
                    time <= datetime.datetime(2019, 6, 19, 4, 17, 0):  # 1248
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [170.5, 170.5, 169.75, 172.85, 173.35,
                              172.85, 172.25]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2015, 8, 3, 22, 45, 0) and \
                    time <= datetime.datetime(2016, 7, 22, 22, 49, 59) or \
                    time >= datetime.datetime(2017, 8, 10, 16, 0, 0) and \
                    time <= datetime.datetime(2018, 6, 25, 0, 0, 0) or \
                    time >= datetime.datetime(2019, 6, 23, 22, 52, 0) and \
                    time <= datetime.datetime(2020, 9, 1, 0, 0, 0):  # 1250
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [168.2, 168.2, 168.05, 169.85, 170.05,
                              169.6, 170.45]
                sens_interpolated = interp1d(f_calib, sens_calib)

        elif node == '/LJ01D':  # Oregon Shelf Base Seafloor
            if time >= datetime.datetime(2018, 6, 30, 2, 30, 0) and \
                    time <= datetime.datetime(2019, 6, 19, 23, 31, 0):  # 1249
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [168.5, 168.5, 167.6, 169.45, 171.85,
                              172.65, 171.7]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2014, 9, 10, 15, 43, 0) and \
                    time <= datetime.datetime(2015, 8, 1, 0, 0, 0) or \
                    time >= datetime.datetime(2016, 7, 22, 22, 50, 0) and \
                    time <= datetime.datetime(2017, 9, 9, 3, 30, 0):  # 1249
                f_calib = [0, 26, 13500, 27100, 40600, 54100]
                sens_calib = [170.53, 170.53, 175.1, 174.5, 174.6, 173.5]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2020, 9, 1, 0, 0, 0):  # 1248
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [170.5, 170.5, 169.75, 172.85, 173.35,
                              172.85, 172.25]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2015, 8, 2, 5, 47, 0) and \
                    time <= datetime.datetime(2016, 7, 22, 22, 49, 59) or \
                    time >= datetime.datetime(2017, 9, 10, 14, 30, 0) and \
                    time <= datetime.datetime(2018, 6, 29, 2, 30, 0):  # 1411
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [168.6, 168.6, 169.2, 170.9, 171.45,
                              171.55, 174.2]
                sens_interpolated = interp1d(f_calib, sens_calib)
            elif time >= datetime.datetime(2019, 6, 23, 3, 36, 0) and \
                    time <= datetime.datetime(2020, 9, 1, 0, 0, 0):  # 1411
                f_calib = [0, 26, 10000, 20100, 30100, 40200, 50200]
                sens_calib = [168.6, 168.6, 168.75, 169.6, 169.65,
                              170.0, 170.2]
                sens_interpolated = interp1d(f_calib, sens_calib)

        else:
            output_array = 169.0 * np.ones(N)
            return output_array

        return sens_interpolated(f)

    def compute_spectrogram(self, win='hann', L=4096, avg_time=None,
                            overlap=0.5, verbose=True):
        """
        Compute spectrogram of acoustic signal. For each time step of the
        spectrogram either a modified periodogram (avg_time=None)
        or a power spectral density estimate using Welch's method with median
        averaging is computed.

        Parameters
        ----------
        win : str, optional
            Window function used to taper the data. See scipy.signal.get_window
            for a list of possible window functions (Default is Hann-window.)
        L : int, optional
            Length of each data block for computing the FFT (Default is 4096).
        avg_time : float, optional
            Time in seconds that is covered in one time step of the
            spectrogram. Default value is None and one time step covers L
            samples. If the signal covers a long time period it is recommended
            to use a higher value for avg_time to avoid memory overflows and
            to facilitate visualization.
        overlap : float, optional
            Percentage of overlap between adjacent blocks if Welch's method is
            used. Parameter is ignored if avg_time is None. (Default is 50%)
        verbose : bool, optional
            If true (defult), exception messages and some comments are printed.

        Returns
        -------
        Spectrogram
            A Spectrogram object that contains time and frequency bins as
            well as corresponding values. If no noise date is available,
            None is returned.
        """
        specgram = []
        time = []

        if any(self.data) is None:
            if verbose:
                print('Data object is empty. Spectrogram cannot be computed')
            self.spectrogram = None
            return None

        # sampling frequency
        fs = self.stats.sampling_rate

        # number of time steps
        if avg_time is None:
            nbins = int((len(self.data) - L) / ((1 - overlap) * L)) + 1
        else:
            nbins = int(np.ceil(len(self.data) / (avg_time * fs)))

        # compute spectrogram. For avg_time=None
        # (periodogram for each time step), the last data samples are ignored
        # if len(noise[0].data) != k * L
        if avg_time is None:
            n_hop = int(L * (1 - overlap))
            for n in range(nbins):
                f, Pxx = signal.periodogram(
                    x=self.data[n * n_hop:n * n_hop + L],
                    fs=fs, window=win)
                if len(Pxx) != int(L / 2) + 1:
                    if verbose:
                        print('Error while computing periodogram for segment',
                              n)
                    self.spectrogram = None
                    return None
                else:
                    calib_time = self.stats.starttime.datetime
                    tmp = self.freq_dependent_sensitivity_correct(
                        int(L / 2 + 1), self.stats.location, calib_time)

                    Pxx = 10 * np.log10(Pxx * np.power(10, tmp / 10)) - 128.9

                    specgram.append(Pxx)
                    time.append(self.stats.starttime.datetime
                                + datetime.timedelta(seconds=n * L / fs))

        else:
            for n in range(nbins - 1):
                f, Pxx = signal.welch(
                    x=self.data[n * int(fs * avg_time):
                                (n + 1) * int(fs * avg_time)],
                    fs=fs, window=win, nperseg=L, noverlap=int(L * overlap),
                    nfft=L, average='median')

                if len(Pxx) != int(L / 2) + 1:
                    if verbose:
                        print('Error while computing '
                              'Welch estimate for segment', n)
                    self.spectrogram = None
                    return None
                else:
                    calib_time = self.stats.starttime.datetime
                    tmp = self.freq_dependent_sensitivity_correct(
                        int(L / 2 + 1), self.stats.location, calib_time)

                    Pxx = 10 * np.log10(Pxx * np.power(10, tmp / 10)) - 128.9
                    specgram.append(Pxx)
                    time.append(self.stats.starttime.datetime
                                + datetime.timedelta(seconds=n * avg_time))

            # compute PSD for residual segment
            # if segment has more than L samples
            if len(self.data[int((nbins - 1) * fs * avg_time):]) >= L:
                f, Pxx = signal.welch(
                    x=self.data[int((nbins - 1) * fs * avg_time):],
                    fs=fs, window=win, nperseg=L, noverlap=int(L * overlap),
                    nfft=L, average='median')
                if len(Pxx) != int(L / 2) + 1:
                    if verbose:
                        print(
                            'Error while computing Welch '
                            'estimate residual segment')
                    self.spectrogram = None
                    return None
                else:
                    calib_time = self.stats.starttime.datetime
                    tmp = self.freq_dependent_sensitivity_correct(
                        int(L / 2 + 1), self.stats.location, calib_time)

                    Pxx = 10 * np.log10(Pxx * np.power(10, tmp / 10)) - 128.9
                    specgram.append(Pxx)
                    time.append(self.stats.starttime.datetime
                                + datetime.timedelta(seconds=(nbins - 1)
                                                     * avg_time))

        if len(time) == 0:
            if verbose:
                print('Spectrogram does not contain any data')
            self.spectrogram = None
            return None
        else:
            self.spectrogram = Spectrogram(np.array(time), np.array(f),
                                           np.array(specgram))
            return self.spectrogram

    #self.data
    #self.stats.sampling_rate
    #self.spectrogram
    #self.stats.starttime.datetime
    #tmp = self.freq_dependent_sensitivity_correct(
                        #int(L / 2 + 1), self.stats.location, calib_time)
    #f, Pxx, Nb = welch_percentile(x=self.data[n * int(fs * avg_time):
                    #            (n + 1) * int(fs * avg_time)],
            #        bias_func=bias_digamma_approx, fs=fs, window=win, nperseg=L,
            #        overlap=0.5, nfft=L, percentile=percentile)
    def compute_spectrogram_wp(self, win='hann', L=4096, avg_time=None,
                            overlap=0.5, verbose=True, percentile=0.5):
        """
        Compute spectrogram of acoustic signal. For each time step of the
        spectrogram either a modified periodogram (avg_time=None)
        or a power spectral density estimate using Welch's method with median
        averaging is computed.

        Parameters
        ----------
        win : str, optional
            Window function used to taper the data. See scipy.signal.get_window
            for a list of possible window functions (Default is Hann-window.)
        L : int, optional
            Length of each data block for computing the FFT (Default is 4096).
        avg_time : float, optional
            Time in seconds that is covered in one time step of the
            spectrogram. Default value is None and one time step covers L
            samples. If the signal covers a long time period it is recommended
            to use a higher value for avg_time to avoid memory overflows and
            to facilitate visualization.
        overlap : float, optional
            Percentage of overlap between adjacent blocks if Welch's method is
            used. Parameter is ignored if avg_time is None. (Default is 50%)
        verbose : bool, optional
            If true (defult), exception messages and some comments are printed.

        Returns
        -------
        Spectrogram
            A Spectrogram object that contains time and frequency bins as
            well as corresponding values. If no noise date is available,
            None is returned.
        """
        specgram = []
        time = []

        if any(self.data) is None:
            if verbose:
                print('Data object is empty. Spectrogram cannot be computed')
            self.spectrogram = None
            return None

        # sampling frequency
        fs = self.stats.sampling_rate

        # number of time steps
        if avg_time is None:
            nbins = int((len(self.data) - L) / ((1 - overlap) * L)) + 1
        else:
            nbins = int(np.ceil(len(self.data) / (avg_time * fs)))

        # compute spectrogram. For avg_time=None
        # (periodogram for each time step), the last data samples are ignored
        # if len(noise[0].data) != k * L
        if avg_time is None:
            n_hop = int(L * (1 - overlap))
            for n in range(nbins):
                #f, Pxx, Nb = welch_percentile(x=self.data[n * n_hop:n * n_hop + L],
                #    bias_func=bias_digamma_approx, fs=fs, window=win, nperseg=L,
                #    overlap=0.5, nfft=L, percentile=percentile)
                f, Pxx = signal.periodogram(
                    x=self.data[n * n_hop:n * n_hop + L],
                    fs=fs, window=win)
                if len(Pxx) != int(L / 2) + 1:
                    if verbose:
                        print('Error while computing periodogram for segment',
                              n)
                    self.spectrogram = None
                    return None
                else:
                    calib_time = self.stats.starttime.datetime
                    tmp = self.freq_dependent_sensitivity_correct(
                        int(L / 2 + 1), self.stats.location, calib_time)

                    Pxx = 10 * np.log10(Pxx * np.power(10, tmp / 10)) - 128.9

                    specgram.append(Pxx)
                    time.append(self.stats.starttime.datetime
                                + datetime.timedelta(seconds=n * L / fs))

        else:
            for n in range(nbins - 1):
                f, Pxx, Nb = welch_percentile(x=self.data[n * int(fs * avg_time):
                                (n + 1) * int(fs * avg_time)],
                    bias_func=bias_digamma_approx, fs=fs, window=win, nperseg=L,
                    overlap=0.5, nfft=L, percentile=percentile)
                #f, Pxx = signal.welch(
                #    x=self.data[n * int(fs * avg_time):
                #                (n + 1) * int(fs * avg_time)],
                #    fs=fs, window=win, nperseg=L, noverlap=int(L * overlap),
                #    nfft=L, average='median')

                if len(Pxx) != int(L / 2) + 1:
                    if verbose:
                        print('Error while computing '
                              'Welch estimate for segment', n)
                    self.spectrogram = None
                    return None
                else:
                    calib_time = self.stats.starttime.datetime
                    tmp = self.freq_dependent_sensitivity_correct(
                        int(L / 2 + 1), self.stats.location, calib_time)

                    Pxx = 10 * np.log10(Pxx * np.power(10, tmp / 10)) - 128.9
                    specgram.append(Pxx)
                    time.append(self.stats.starttime.datetime
                                + datetime.timedelta(seconds=n * avg_time))

            # compute PSD for residual segment
            # if segment has more than L samples
            if len(self.data[int((nbins - 1) * fs * avg_time):]) >= L:
                f, Pxx, Nb = welch_percentile(x=self.data[int((nbins - 1) * fs * avg_time):],
                    bias_func=bias_digamma_approx, fs=fs, window=win, nperseg=L,
                    overlap=0.5, nfft=L, percentile=percentile)
                #f, Pxx = signal.welch(
                #    x=self.data[int((nbins - 1) * fs * avg_time):],
                #    fs=fs, window=win, nperseg=L, noverlap=int(L * overlap),
                #    nfft=L, average='median')
                if len(Pxx) != int(L / 2) + 1:
                    if verbose:
                        print(
                            'Error while computing Welch '
                            'estimate residual segment')
                    self.spectrogram = None
                    return None
                else:
                    calib_time = self.stats.starttime.datetime
                    tmp = self.freq_dependent_sensitivity_correct(
                        int(L / 2 + 1), self.stats.location, calib_time)

                    Pxx = 10 * np.log10(Pxx * np.power(10, tmp / 10)) - 128.9
                    specgram.append(Pxx)
                    time.append(self.stats.starttime.datetime
                                + datetime.timedelta(seconds=(nbins - 1)
                                                     * avg_time))

        if len(time) == 0:
            if verbose:
                print('Spectrogram does not contain any data')
            self.spectrogram = None
            return None
        else:
            self.spectrogram = Spectrogram(np.array(time), np.array(f),
                                           np.array(specgram))
            return self.spectrogram




    def compute_spectrogram_mp(self, n_process=None, win='hann', L=4096,
                               avg_time=None, overlap=0.5, verbose=True):
        """
        Same as function compute_spectrogram but using multiprocessing.
        This function is intended to be used when analyzing large data sets.

        Parameters
        ----------
        n_process : int, optional
            Number of processes in the pool. None (default) means that
            n_process is equal to the number of CPU cores.
        win : str, optional
            Window function used to taper the data.
            See scipy.signal.get_window for a list of possible window functions
            (Default is Hann-window.)
        L : int, optional
            Length of each data block for computing the FFT (Default is 4096).
        avg_time : float, optional
            Time in seconds that is covered in one time step of the
            spectrogram. Default value is None and one time step covers L
            samples. If the signal covers a long time period it is recommended
            to use a higher value for avg_time to avoid memory overflows and
            to facilitate visualization.
        overlap : float, optional
            Percentage of overlap between adjacent blocks if Welch's method
            is used. Parameter is ignored if avg_time is None. (Default is 50%)
        verbose : bool, optional
            If true (defult), exception messages and some comments are printed.

        Returns
        -------
        Spectrogram
            A Spectrogram object that contains time and frequency bins as well
            as corresponding values. If no noise date is available,
            None is returned.
        """

        # create array with N start and end time values
        if n_process is None:
            N = mp.cpu_count()
        else:
            N = n_process

        ooi_hyd_data_list = []
        seconds_per_process = (self.stats.endtime - self.stats.starttime) / N
        for k in range(N - 1):
            starttime = self.stats.starttime + datetime.timedelta(
                seconds=k * seconds_per_process)
            endtime = self.stats.starttime + datetime.timedelta(
                seconds=(k + 1) * seconds_per_process)
            temp_slice = self.slice(starttime=UTCDateTime(starttime),
                                    endtime=UTCDateTime(endtime))
            tmp_obj = HydrophoneData(data=temp_slice.data,
                                     header=temp_slice.stats)
            ooi_hyd_data_list.append((tmp_obj, win, L, avg_time, overlap))

        starttime = self.stats.starttime + datetime.timedelta(
            seconds=(N - 1) * seconds_per_process)
        temp_slice = self.slice(starttime=UTCDateTime(starttime),
                                endtime=UTCDateTime(self.stats.endtime))
        tmp_obj = HydrophoneData(data=temp_slice.data, header=temp_slice.stats)
        ooi_hyd_data_list.append((tmp_obj, win, L, avg_time, overlap))

        with mp.get_context("spawn").Pool(n_process) as p:
            try:
                specgram_list = p.starmap(_spectrogram_mp_helper,
                                          ooi_hyd_data_list)
                # concatenate all small spectrograms to
                # obtain final spectrogram
                specgram = []
                time_specgram = []
                for i in range(len(specgram_list)):
                    time_specgram.extend(specgram_list[i].time)
                    specgram.extend(specgram_list[i].values)
                self.spectrogram = Spectrogram(np.array(time_specgram),
                                               specgram_list[0].freq,
                                               np.array(specgram))
                return self.spectrogram
            except Exception:
                if verbose:
                    print('Cannot compute spectrogram')
                self.spectrogram = None
                return None

    def compute_psd_welch(self, win='hann', L=4096, overlap=0.5,
                          avg_method='median', interpolate=None, scale='log',
                          verbose=True):
        """
        Compute power spectral density estimates of noise data using
        Welch's method.

        Parameters
        ----------
        win : str, optional
            Window function used to taper the data. See scipy.signal.get_window
            for a list of possible window functions (Default is Hann-window.)
        L : int, optional
            Length of each data block for computing the FFT (Default is 4096).
        overlap : float, optional
            Percentage of overlap between adjacent blocks if Welch's method is
            used. Parameter is ignored if avg_time is None. (Default is 50%)
        avg_method : str, optional
            Method for averaging the periodograms when using Welch's method.
            Either 'mean' or 'median' (default) can be used
        interpolate : float, optional
            Resolution in frequency domain in Hz. If None (default), the
            resolution will be sampling frequency fs divided by L. If
            interpolate is smaller than fs/L, the PSD will be interpolated
            using zero-padding
        scale : str, optional
            If 'log' (default) PSD in logarithmic scale (dB re 1µPa^2/H) is
            returned. If 'lin', PSD in linear scale
            (1µPa^2/H) is returned
        verbose : bool, optional
            If true (default), exception messages and some comments are
            printed.

        Returns
        -------
        Psd
            A Psd object that contains frequency bins and PSD values. If no
            noise date is available, None is returned.
        """
        # get noise data segment for each entry in rain_event
        # each noise data segment contains usually 1 min of data
        if any(self.data) is None:
            if verbose:
                print('Data object is empty. PSD cannot be computed')
            self.psd = None
            return None
        fs = self.stats.sampling_rate

        # compute nfft if zero padding is desired
        if interpolate is not None:
            if fs / L > interpolate:
                nfft = int(fs / interpolate)
            else:
                nfft = L
        else:
            nfft = L

        # compute Welch median for entire data segment
        f, Pxx = signal.welch(x=self.data, fs=fs, window=win, nperseg=L,
                              noverlap=int(L * overlap),
                              nfft=nfft, average=avg_method)

        if len(Pxx) != int(nfft / 2) + 1:
            if verbose:
                print('PSD cannot be computed.')
            self.psd = None
            return None

        calib_time = self.stats.starttime.datetime
        sense_corr = self.freq_dependent_sensitivity_correct(
            int(nfft / 2 + 1), self.stats.location, calib_time)
        if scale == 'log':
            Pxx = 10 * np.log10(Pxx * np.power(10, sense_corr / 10)) - 128.9
        elif scale == 'lin':
            Pxx = Pxx * np.power(10, sense_corr / 10) * \
                np.power(10, -128.9 / 10)
        else:
            raise Exception('scale has to be either "lin" or "log".')

        self.psd = Psd(f, Pxx)
        return self.psd

    def compute_psd_welch_mp(self, split, n_process=None, win='hann', L=4096,
                             overlap=0.5, avg_method='median',
                             interpolate=None, scale='log', verbose=True):
        """
        Same as compute_psd_welch but using the multiprocessing library.

        Parameters
        ----------
        split : int, float, or array of datetime.datetime
            Time period for each PSD estimate. The time between start_time and
            end_time is split into parts of length
            split seconds (if float). The last segment can be shorter than
            split seconds. Alternatively split can
            be set as an list, where each entry is a start-end time tuple.
        n_process : int, optional
            Number of processes in the pool. None (default) means that
            n_process is equal to the number
            of CPU cores.
        win : str, optional
            Window function used to taper the data. See scipy.signal.get_window
            for a list of possible window functions (Default is Hann-window.)
        L : int, optional
            Length of each data block for computing the FFT (Default is 4096).
        overlap : float, optional
            Percentage of overlap between adjacent blocks if Welch's method is
            used. Parameter is ignored if avg_time is None. (Default is 50%)
        avg_method : str, optional
            Method for averaging the periodograms when using Welch's method.
            Either 'mean' or 'median' (default) can be used
        interpolate : float, optional
            Resolution in frequency domain in Hz. If None (default), the
            resolution will be sampling frequency fs divided by L. If
            interpolate is smaller than fs/L, the PSD will be interpolated
            using zero-padding
        scale : str, optional
            If 'log' (default) PSD in logarithmic scale (dB re 1µPa^2/H) is
            returned. If 'lin', PSD in linear scale (1µPa^2/H) is returned
        verbose : bool, optional
            If true (default), exception messages and some comments are
            printed.

        Returns
        -------
        list of Psd
            A list of Psd objects where each entry represents the PSD of the
            respective noise segment. If no noise data is available, None is
            returned.
        """

        # create array with N start and end time values
        if n_process is None:
            n_process = mp.cpu_count()

        ooi_hyd_data_list = []
        # do segmentation from scratch
        if isinstance(split, int) or isinstance(split, float):
            n_seg = int(
                np.ceil((self.stats.endtime - self.stats.starttime) / split))

            seconds_per_process = \
                (self.stats.endtime - self.stats.starttime) / n_seg

            for k in range(n_seg - 1):
                starttime = self.stats.starttime + datetime.timedelta(
                    seconds=k * seconds_per_process)
                endtime = self.stats.starttime + datetime.timedelta(
                    seconds=(k + 1) * seconds_per_process)
                temp_slice = self.slice(starttime=UTCDateTime(starttime),
                                        endtime=UTCDateTime(endtime))
                tmp_obj = HydrophoneData(data=temp_slice.data,
                                         header=temp_slice.stats)
                ooi_hyd_data_list.append(
                    (tmp_obj, win, L, overlap, avg_method, interpolate, scale))

            # treat last segment separately as its length may differ from other
            # segments
            starttime = self.stats.starttime + datetime.timedelta(
                seconds=(n_seg - 1) * seconds_per_process)
            temp_slice = self.slice(starttime=UTCDateTime(starttime),
                                    endtime=UTCDateTime(self.stats.endtime))
            tmp_obj = HydrophoneData(data=temp_slice.data,
                                     header=temp_slice.stats)
            ooi_hyd_data_list.append(
                (tmp_obj, win, L, overlap, avg_method, interpolate, scale))
        # use segmentation specified by split
        else:
            ooi_hyd_data_list = []
            for row in split:
                temp_slice = self.slice(starttime=UTCDateTime(row[0]),
                                        endtime=UTCDateTime(row[1]))
                tmp_obj = HydrophoneData(data=temp_slice.data,
                                         header=temp_slice.stats)
                ooi_hyd_data_list.append(
                    (tmp_obj, win, L, overlap, avg_method, interpolate, scale))

        with mp.get_context("spawn").Pool(n_process) as p:
            try:
                self.psd_list = p.starmap(_psd_mp_helper, ooi_hyd_data_list)
            except Exception:
                if verbose:
                    print('Cannot compute PSd list')
                self.psd_list = None

        return self.psd_list

    def wav_write(self, filename, norm=False, new_sample_rate=None):
        '''
        method that stores HydrophoneData into .wav file

        Parameters
        ----------
        filename : str
            filename to store .wav file as
        norm : bool
            specifices whether data should be normalized to 1
        new_sample_rate : float
            specifices new sample rate of wav file to be saved. (Resampling is
            done with scipy.signal.resample()). Default is None which keeps
            original sample rate of data.
        '''
        if norm:
            data = self.data / np.abs(np.max(self.data))
        else:
            data = self.data

        if new_sample_rate is None:
            sampling_rate = self.stats.sampling_rate
        else:
            if new_sample_rate > self.stats.sampling_rate:
                upsamp_fac = new_sample_rate / self.stats.sampling_rate
                new_npts = self.stats.npts * upsamp_fac
                data = signal.resample(data, int(new_npts))
                sampling_rate = new_sample_rate
            elif new_sample_rate == self.stats.sampling_rate:
                warnings.warn('New sample rate is same as original data. '
                              'No resampling done.')
                sampling_rate = self.stats.sampling_rate
            elif new_sample_rate < self.stats.sampling_rate:
                warnings.warn('New sample rate is lower than original sample'
                              ' rate. Chebychev 1 anti-aliasing filter used')
                if self.stats.sampling_rate % new_sample_rate != 0:
                    raise Exception(
                        'New Sample Rate is not factor of original sample rate'
                    )
                else:
                    data = signal.decimate(
                        data, int(self.stats.sampling_rate / new_sample_rate))
                    sampling_rate = new_sample_rate

        wavfile.write(filename, int(sampling_rate), data)


def _spectrogram_mp_helper(ooi_hyd_data_obj, win, L, avg_time, overlap):
    """
    Helper function for compute_spectrogram_mp
    """
    ooi_hyd_data_obj.compute_spectrogram(win, L, avg_time, overlap)
    return ooi_hyd_data_obj.spectrogram


def _psd_mp_helper(ooi_hyd_data_obj, win, L, overlap, avg_method, interpolate,
                   scale):
    """
    Helper function for compute_psd_welch_mp
    """
    ooi_hyd_data_obj.compute_psd_welch(win, L, overlap, avg_method,
                                       interpolate, scale)
    return ooi_hyd_data_obj.psd


class Spectrogram:
    """
    A class used to represent a spectrogram object.

    Attributes
    ----------
    time : 1-D array of float or datetime objects
        Indices of time-bins of spectrogram.
    freq : 1-D array of float
        Indices of frequency-bins of spectrogram.
    values : 2-D array of float
        Values of the spectrogram. For each time-frequency-bin pair there has
        to be one entry in values. That is, if time has  length N and freq
        length M, values is a NxM array.

    """

    def __init__(self, time, freq, values):
        self.time = time
        self.freq = freq
        self.values = values

    def visualize(self, plot_spec=True, save_spec=False,
                  filename='spectrogram.png', title='spectrogram',
                  xlabel='time', xlabel_rot=70, ylabel='frequency', fmin=0,
                  fmax=32000, vmin=20, vmax=80, vdelta=1.0,
                  vdelta_cbar=5, figsize=(16, 9), dpi=96, res_reduction_time=1,
                  res_reduction_freq=1, time_limits=None):
        """
        This function will be depreciated into a differnt module in the future.
        The current documentation might not be accurate.

        To plot spectrograms please see
        :meth:`ooipy.hydrophone.basic.plot_spectrogram`

        Basic visualization of spectrogram based on matplotlib. The function
        offers two options: Plot spectrogram in Python (plot_spec = True) and
        save spectrogram plot in directory (save_spec = True). Spectrograms are
        plotted in dB re 1µ Pa^2/Hz.

        plot_spec (bool): whether or not spectrogram is plotted using Python
        save_spec (bool): whether or not spectrogram plot is saved
        filename (str): directory where spectrogram plot is saved. Use ending
        ".png" or ".pdf" to save as PNG or PDF file. This value will be ignored
        if save_spec=False
        title (str): title of plot
        ylabel (str): label of vertical axis
        xlabel (str): label of horizontal axis
        xlabel_rot (float): rotation of xlabel. This is useful if xlabel are
        longer strings for example when using datetime.datetime objects.
        fmin (float): minimum frequency (unit same as f) that is displayed
        fmax (float): maximum frequency (unit same as f) that is displayed
        vmin (float): minimum value (dB) of spectrogram that is colored.
        All values below are displayed in white.
        vmax (float): maximum value (dB) of spectrogram that is colored.
        All values above are displayed in white.
        vdelta (float): color resolution
        vdelta_cbar (int): label ticks in colorbar are in vdelta_cbar steps
        figsize (tuple(int)): size of figure
        dpi (int): dots per inch
        time_limits : list
            specifices xlimits on spectrogram. List contains two
            datetime.datetime objects
        """
        import warnings
        raise warnings.warn('will be depricated in future. Please see '
                            'ooipy.tools.ooiplotlib.plot_spectrogram()')
        # set backend for plotting/saving:
        if not plot_spec:
            matplotlib.use('Agg')

        font = {'size': 22}
        matplotlib.rc('font', **font)

        v = self.values[::res_reduction_time, ::res_reduction_freq]

        if len(self.time) != len(self.values):
            t = np.linspace(0, len(self.values) - 1,
                            int(len(self.values) / res_reduction_time))
        else:
            t = self.time[::res_reduction_time]

        # Convert t to np.array of datetime.datetime
        if type(t[0]) == UTCDateTime:
            for k in range(len(t)):
                t[k] = t[k].datetime

        if len(self.freq) != len(self.values[0]):
            f = np.linspace(0, len(self.values[0]) - 1,
                            int(len(self.values[0]) / res_reduction_freq))
        else:
            f = self.freq[::res_reduction_freq]

        cbarticks = np.arange(vmin, vmax + vdelta, vdelta)
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        im = ax.contourf(t, f, np.transpose(v), cbarticks,
                         norm=colors.Normalize(vmin=vmin, vmax=vmax),
                         cmap=plt.cm.jet)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.ylim([fmin, fmax])
        if time_limits is not None:
            plt.xlim(time_limits)
        plt.xticks(rotation=xlabel_rot)
        plt.title(title)
        plt.colorbar(im, ax=ax,
                     ticks=np.arange(vmin, vmax + vdelta, vdelta_cbar))
        plt.tick_params(axis='y')

        if type(t[0]) == datetime.datetime:
            ax.xaxis.set_major_formatter(
                mdates.DateFormatter('%y-%m-%d %H:%M'))

        if save_spec:
            plt.savefig(filename, dpi=dpi, bbox_inches='tight')

        if plot_spec:
            plt.show()
        else:
            plt.close(fig)

    def save(self, filename='spectrogram.pickle'):
        """
        !!!!! This function will be moved into a different module in the
        future. The current documentation might not be accurate !!!!!

        Save spectrogram in pickle file.

        filename (str): directory where spectrogram data is saved. Ending has
        to be ".pickle".
        """

        dct = {
            't': self.time,
            'f': self.freq,
            'spectrogram': self.values
        }
        with open(filename, 'wb') as outfile:
            pickle.dump(dct, outfile)

    def plot(self, **kwargs):
        '''
        redirects to ooipy.ooiplotlib.plot_spectrogram()
        please see :meth:`ooipy.hydrophone.basic.plot_spectrogram`
        '''
        ooipy.tools.ooiplotlib.plot_spectrogram(self, **kwargs)


class Psd:
    """
    A calss used to represent a PSD object

    Attributes
    ----------
    freq : array of float
        Indices of frequency-bins of PSD.
    values : array of float
        Values of the PSD.

    TODO:
    Methods
    -------
    visualize(plot_psd=True, save_psd=False, filename='psd.png', title='PSD',
    xlabel='frequency', xlabel_rot=0, ylabel='spectral level', fmin=0,
    fmax=32, vmin=20, vmax=80, figsize=(16,9), dpi=96)
        Visualizes PSD estimate using matplotlib.
    save(filename='psd.json', ancillary_data=[], ancillary_data_label=[])
        Saves PSD estimate and ancillary data in .json file.
    """

    def __init__(self, freq, values):
        self.freq = freq
        self.values = values

    def visualize(self, plot_psd=True, save_psd=False, filename='psd.png',
                  title='PSD', xlabel='frequency',
                  xlabel_rot=0, ylabel='spectral level', fmin=0, fmax=32000,
                  vmin=20, vmax=80, figsize=(16, 9), dpi=96):
        """
        !!!!! This function will be moved into a different module in the
        future. The current documentation might not be accurate !!!!!

        Basic visualization of PSD estimate based on matplotlib. The function
        offers two options: Plot PSD in Python (plot_psd = True) and save PSD
        plot in directory (save_psd = True). PSDs are plotted in dB re 1µ
        Pa^2/Hz.

        plot_psd (bool): whether or not PSD is plotted using Python
        save_psd (bool): whether or not PSD plot is saved
        filename (str): directory where PSD plot is saved. Use ending ".png"
        or ".pdf" to save as PNG or PDF
            file. This value will be ignored if save_psd=False
        title (str): title of plot
        ylabel (str): label of vertical axis
        xlabel (str): label of horizontal axis
        xlabel_rot (float): rotation of xlabel. This is useful if xlabel are
        longer strings.
        fmin (float): minimum frequency (unit same as f) that is displayed
        fmax (float): maximum frequency (unit same as f) that is displayed
        vmin (float): minimum value (dB) of PSD.
        vmax (float): maximum value (dB) of PSD.
        figsize (tuple(int)): size of figure
        dpi (int): dots per inch
        """
        import warnings
        raise warnings.warn('will be depricated in future. Please see '
                            'ooipy.tools.ooiplotlib.plot_psd()')
        # set backend for plotting/saving:
        if not plot_psd:
            matplotlib.use('Agg')

        font = {'size': 22}
        matplotlib.rc('font', **font)

        if len(self.freq) != len(self.values):
            f = np.linspace(0, len(self.values) - 1, len(self.values))
        else:
            f = self.freq

        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        plt.semilogx(f, self.values)
        plt.ylabel(ylabel)
        plt.xlabel(xlabel)
        plt.xlim([fmin, fmax])
        plt.ylim([vmin, vmax])
        plt.xticks(rotation=xlabel_rot)
        plt.title(title)
        plt.grid(True)

        if save_psd:
            plt.savefig(filename, dpi=dpi, bbox_inches='tight')

        if plot_psd:
            plt.show()
        else:
            plt.close(fig)

    def save(self, filename='psd.json', ancillary_data=[],
             ancillary_data_label=[]):
        """
        !!!!! This function will be moved into a different module in the
        future. The current documentation might not be accurate !!!!!

        Save PSD estimates along with with ancillary data
        (stored in dictionary) in json file.

        filename (str): directory for saving the data
        ancillary_data ([array like]): list of ancillary data
        ancillary_data_label ([str]): labels for ancillary data used as keys
        in the output dictionary.
            Array has same length as ancillary_data array.
        """

        if len(self.freq) != len(self.values):
            f = np.linspace(0, len(self.values) - 1, len(self.values))
        else:
            f = self.freq

        if type(self.values) != list:
            values = self.values.tolist()

        if type(f) != list:
            f = f.tolist()

        dct = {
            'psd': values,
            'f': f
        }

        if len(ancillary_data) != 0:
            for i in range(len(ancillary_data)):
                if type(ancillary_data[i]) != list:
                    dct[ancillary_data_label[i]] = ancillary_data[i].tolist()
                else:
                    dct[ancillary_data_label[i]] = ancillary_data[i]

        with open(filename, 'w+') as outfile:
            json.dump(dct, outfile)

    def plot(self, **kwargs):
        '''
        redirects to ooipy.ooiplotlib.plot_psd()
        please see :meth:`ooipy.hydrophone.basic.plot_psd`
        '''
        ooipy.tools.ooiplotlib.plot_psd(self, **kwargs)


def compute_nu(N, Ns, win, o):
    Nb = int(N/(Ns*(1-o)))
    def _sum_win(win, Ns, m, o):
        win_s = np.roll(win, -int((1-o)*Ns)*m)
        win_s[-int((1-o)*Ns)*m:] = 0
        return abs(np.sum(win * win_s))**2
    sum_denom = 0
    for m in np.linspace(1, Nb-1, Nb-1, dtype=int):
        sum_denom += (1 - m/Nb)*_sum_win(win, Ns, m, o)
    nu = 2*Nb / (1 + 2 * sum_denom)
    return nu

# parts are from https://github.com/scipy/scipy/blob/v1.5.2/scipy/signal/spectral.py#L291-L454
def welch_percentile(x, bias_func, fs=1.0, window='hann', nperseg=None, overlap=None, nfft=None,
        detrend='constant', return_onesided=True, scaling='density',
        axis=-1, percentile=None, numRV='edof'):

    freqs, _, Pxy = signal.spectral._spectral_helper(x, x, fs, window, nperseg, int(nperseg * overlap), nfft,
                                            detrend, return_onesided, scaling, axis,
                                            mode='psd')
    
    Nb = Pxy.shape[-1]

    if len(Pxy.shape) >= 2 and Pxy.size > 0:
        if Pxy.shape[-1] > 1:
            if percentile == None:
                Pxy = Pxy.mean(axis=-1)
            elif isinstance(percentile, int) or isinstance(percentile, float):
                if percentile >= 0 and percentile <= 1:
                    
                    if numRV == 'n':
                        Pxy = np.quantile(Pxy, percentile, axis=-1) / bias_func(Pxy.shape[-1], percentile)
                    elif numRV == 'edof':
                        win = signal.get_window(window, nperseg) / np.sqrt(np.sum(signal.get_window(window, nperseg)**2))
                        edof = compute_nu(len(x), nperseg, win, overlap)
                        if bias_func == bias_digamma_approx:
                            Pxy = np.quantile(Pxy, percentile, axis=-1) / bias_func(edof / 2, percentile)
                        else:
                            Pxy = np.quantile(Pxy, percentile, axis=-1) / bias_func(int(np.round(edof / 2)), percentile)
                else:
                    raise ValueError('percentile must be between 0 and 1, got %s'
                                    % (percentile,))
            else:
                raise ValueError('percentile must be integer, float, or None type, got type %s'
                                    % (type(percentile),))
        else:
            Pxy = np.reshape(Pxy, Pxy.shape[:-1])
    
    return freqs, Pxy, Nb

def bias_alternating_harmonic_series(N, p):
    l = np.linspace(1, N, N)
    return np.sum((-1)**(l+1)/l)

def bias_truncated_harmonic_series(N, p):
    percentiles = np.round(np.linspace(1/(N+1), 1 - 1/(N+1), N), 3)
    if p in percentiles:
        l = np.arange(np.round((N-1)*(1-p)) + 1, N+1, 1)
    else:
        l = np.arange(np.round(N*(1-p)) + 1, N+2, 1)
    return np.sum(1/l)

def bias_digamma_approx(N, p):
    def digamma(x):
        return np.log(x) - 1/(2*x) - 1/(12*x**2) + 1/(120*x**4) - 1/(252*x**6)
    
    return digamma(N+2) - digamma(N*(1-p)+1)

def no_bias_correct(N, p):
    return 1.0

def bias_limit(N, p):
    return -np.log(1-p)