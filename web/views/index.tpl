<div class="row">
    <div class="col-lg-6 col-md-6 col-sm-12 col-xs-12">
        <div class="row">
            <div class="col-sm-12"><h2>Destinations</h2></div>
            % for d in destinations:
                <div class="col-sm-12">
                    <span class="glyphicon glyphicon-hdd"></span>
                    <strong>{{ d['path'] }}</strong>
                    <br />
                    % used = d['size'] - d['avail']
                    % used_pc = (used / float(d['size'])) * 100.0
                    {{ util.format_bytes(d['avail']) }}/{{ util.format_bytes(d['size']) }} available,
                    {{ util.format_bytes(used) }} used
                    <br />
                    <div class="progress">
                        <div
                            class="progress-bar"
                            role="progressbar"
                            aria-valuenow="{{ used_pc }}"
                            aria-valuemin="0"
                            aria-valuemax="100"
                            style="min-width: 2em; width: {{ used_pc }}%;"
                        >
                            {{ '{:0.2f}%'.format(used_pc) }}
                        </div>
                    </div>
                </div>
            % end
        </div>
    </div>

    <div class="col-lg-6 col-md-6 col-sm-12 col-xs-12">
        <div class="row">
            <div class="col-sm-12"><h2>Cards</h2></div>
            % for card, data in cards.items():
                % size_pc = (data['size'] / float(total_size)) * 100.0
                <div class="col-sm-12">
                    <span class="glyphicon glyphicon-camera"></span>
                    <strong>{{ card }}</strong>
                    <br />
                    {{ util.format_bytes(data['size']) }}, {{ data['files'] }} files
                    <br />
                    <div class="progress">
                        <div
                            class="progress-bar"
                            role="progressbar"
                            aria-valuenow="{{ size_pc }}"
                            aria-valuemin="0"
                            aria-valuemax="100"
                            style="min-width: 2em; width: {{ size_pc }}%;"
                        >
                            {{ '{:0.2f}%'.format(size_pc) }}
                        </div>
                    </div>
                </div>
            % end
        </div>
    </div>
</div>

% rebase('base.tpl', title='AutoDL')
