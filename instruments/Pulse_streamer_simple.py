from pulsestreamer import PulseStreamer, Sequence    

class PulseStreamer_simple():  

    def __init__(self, address = '169.254.8.2'):
        """
        Uses the pulsestreamer python package which can be installed at:
            https://www.swabianinstruments.com/downloads/
            (pulsestreamer-1.1.0-py2.py3-none-any.whl)
        Following user manual:
            https://www.swabianinstruments.com/static/documentation/PulseStreamer/PulseStreamer_User_Manual.pdf
        Connects via the permanent static fallback ip address: 169.254.8.2  
        Licence is
        """
        self.ip = address
        self.ps = PulseStreamer(self.ip)
        self.block =[]
        self.blockchain = self.ps.createSequence()
        
    def create_block(self, block=[('duration', 'level'),(1000, 1)]):
        """
        Creates a single block pattern using run time encoding, takes (duration, level) in ns and V        
        """
        self.block = block
        return block
        
    def load_digital (self, channel, block):
        """
        adds block to blockchain to a given channel
        """
        self.blockchain.setDigital(channel, block)

    def load_analog (self, channel, block):
        """
        adds block to blockchain to a given channel
        """
        self.blockchain.setAnalog(channel, block)

        
    def stream(self, n_runs= PulseStreamer.REPEAT_INFINITELY):
        """
        Sends pulse sequence object (blockchain) to Pulse Streamer
        sequence repeated n_runs times
        """
        self.ps.stream(self.blockchain, n_runs)
    
    def plot_blockchain(self):
        """
        plots whole of blockchain
            * would be good to plot a single block or just digital (only works for Matlab)
        """
        self.blockchain.plot()
        
    def isrunning(self):
        """
        returns yes if Pulse Streamer is running, no otherwise
        """
        if (self.ps.isStreaming()==1):
            print('Yes')
        else:
            print('No') 
            
    def upload_stream_dictionary (self, stream_dict):
        
        for i in range (8):
            self.load_digital (channel = i, block = stream_dict['D'+str(i)])
        
        for i in range (2):
            self.load_analog (channel = i, block = stream_dict['A'+str(i)])

       
    def reset(self):
        """
        resets Pulse Streamer to default state
        all outputs are set to 0V
        does not clear loaded pulses
        """
        self.ps.reset()
        
    def id (self):
        print ("\nSerial number: \n", self.ps.getSerial())
        print("\nFirmware version: \n", self.ps.getFirmwareVersion())
        print("\nIP address: \n", self.ip)

if __name__ == "__main__":
    
    rm = PulseStreamer_simple()
    # Create pulse sequences using run-length encoding
    P1 = rm.create_block(([1000,1],[3000,0]))
    P2 = rm.create_block(([1000,0],[3000,1], [1000,0]))
    P3 = rm.create_block(([1000,0],[3000,1], [1000,0]))
    
    # Place sequences into channels
    rm.load_sequence(channel=0, block=P1+P3+P2)
    rm.load_sequence(channel=6, block=P2+P3)
    
    # plot 
    rm.plot_blockchain()
    
    # stream blockchain
    rm.stream()
    rm.isrunning()
    rm.reset()
    
"""
ToDo:
Export/save blocks
Repeat/concatenate blocks(?)
"""