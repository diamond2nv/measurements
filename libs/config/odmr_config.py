config = {}

config ['system'] = {
	
		'time_unit_ns':		1,
}

config ['streamer_channels'] = {
		'tagger_trigger': 	'D0',
		'off_res_laser':	'D1',
		'res_laser':		'D2',
		'trigger_awg':		'D3',
		'PM_channel':		'D4',
		'I_channel': 		'A0',
		'Q_channel':		'A1',
}

config ['trigger'] = {
		'duration':			50,
		'wait_before':		5,
		'wait_after':		5,
}