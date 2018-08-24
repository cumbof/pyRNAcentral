#!/usr/bin/env python
# http://rnacentral.org/api

import sys, os, optparse, requests, json

### app ###
__version__ = '1.0.0'

#### RNAcentral ####
__rnacentral_api_url__ = 'http://rnacentral.org/api/v1/rna/'
__rnacentral_api_xrefs_url__ = 'http://rnacentral.org/api/v1/rna/__ID__/xrefs'
__rnacentral_api_version__ = 'v1'

### exit codes ###
ERR_EXIT_CODE = 2
OK_EXIT_CODE = 0

def raiseException( exitcode, message, output_dir_path, errorfilename=None ):
    if errorfilename != None:
        errorfilepath = os.path.join( output_dir_path, errorfilename + '_txt' )
        with open(errorfilepath, 'w') as out:
            out.write(message)
    sys.exit(exitcode)

def format_metadata( xrefs_json_content ):
    metadata = { }
    result_count = 0
    if 'results' in xrefs_json_content:
        result_count += 1
        for result in xrefs_json_content['results']:
            for attribute in result:
                if isinstance( result[attribute], dict ): # collapse dictionaries
                    dict_value = dict(result[attribute])
                    for dict_attr in dict_value:
                        extended_attribute = attribute + '__' + dict_attr
                        if not extended_attribute in metadata:
                            metadata[extended_attribute] = [ ]
                            if result_count > 1:
                                metadata[extended_attribute] = [ 'None' ] * ( result_count - 1 )
                        metadata[extended_attribute].append( str(dict_value[dict_attr]) )
                elif isinstance( result[attribute], list ): # skip arrays
                    continue
                else:
                    if not attribute in metadata:
                        metadata[attribute] = [ ]
                        if result_count > 1:
                            metadata[attribute] = [ 'None' ] * ( result_count - 1 )
                    metadata[attribute].append( str(result[attribute]) )
            # fix the arrays size
            for attribute in metadata:
                if len(metadata[attribute]) < result_count:
                    metadata[attribute].append( 'None' )
            result_count += 1
    return metadata, result_count-1

# rnacentral_id is case sensitive
def query_rnacentral( options, args, rnacentral_ids ):
    fasta_dir_path = options.fastadir
    metadata_dir_path = options.metadir
    # set the content type to application/json
    headers = {'Content-type': 'application/json'}
    # create a session
    session = requests.Session()
    for rnacentral_id in rnacentral_ids:
        rnacentral_id = rnacentral_id.split('_')[0]
        # make a get request to the rnacentral apis
        query_url = __rnacentral_api_url__ + rnacentral_id
        req = session.get(query_url, headers=headers)
        resp_code = req.status_code
        #print(str(req.content)+"\n\n");
        if resp_code == requests.codes.ok:
            resp_content = str(req.content)
            # convert out to json
            json_content = json.loads(resp_content)
            # status variable
            something_wrong = False
            # create a metadata file for the current rnacentral_id
            metadata_file_path = os.path.join( metadata_dir_path, rnacentral_id + '.tsv' )
            open(metadata_file_path, 'a').close()
            metadata_xrefs_url = __rnacentral_api_xrefs_url__.replace( '__ID__', rnacentral_id )
            xrefs_req = session.get(metadata_xrefs_url, headers=headers)
            xrefs_resp_code = xrefs_req.status_code
            if xrefs_resp_code == requests.codes.ok:
                xrefs_resp_content = str(xrefs_req.content)
                xrefs_json_content = json.loads(xrefs_resp_content)
                metadata, levels = format_metadata( xrefs_json_content )
                if len(metadata) > 0:
                    #print metadata;
                    #print "levels: " + str(levels);
                    # write metadata on metadata_file_path
                    metadata_file = open(metadata_file_path, 'w')
                    header_line = ''
                    for header_attribute in metadata.keys():
                        header_line += header_attribute + '\t'
                    metadata_file.write( header_line.strip() + '\n' )
                    for level in range(0, levels):
                        metadata_file.write( '\t'.join(metadata[attribute][level] for attribute in metadata ) + '\n' )
                    metadata_file.close()
                else:
                    something_wrong = True
            # create a fasta file for the current rnacentral_id
            fasta_file_path = os.path.join( fasta_dir_path, rnacentral_id + '.fasta' )
            fasta_file = open(fasta_file_path, 'w')
            fasta_file.write( '> %s\n' % rnacentral_id )
            # each line of a sequence should have fewer than 80 characters
            # use 60 as limit
            chunks, chunk_size = len( json_content['sequence'] ), 60
            seq_split = [ json_content['sequence'][i:i+chunk_size] for i in range(0, chunks, chunk_size) ]
            for seq_part in seq_split:
                fasta_file.write( seq_part + '\n' )
            fasta_file.close()
            if not something_wrong:
                yield rnacentral_id, OK_EXIT_CODE
            else:
                yield rnacentral_id, ERR_EXIT_CODE
        else:
            yield rnacentral_id, ERR_EXIT_CODE

def retrieve_data( options, args ):
    errorfile = None
    if options.errorfile:
        errorfile = str(options.errorfile)
    rnacentral_ids = [ ]
    if options.id:
        if ' ' in options.id or '\t' in options.id:
            print 'Error: the RNAcentral ID is not well formatted'
            return raiseException( ERR_EXIT_CODE, "Error: the RNAcentral ID is not well formatted", "./", errorfile )
        rnacentral_ids.append( options.id )
    elif options.file:
        with open(options.file) as file:
            for line in file:
                line = line.strip()
                if line != '':
                    if ' ' in line or '\t' in line:
                        print 'Error: the input file is not well formatted'
                        return raiseException( ERR_EXIT_CODE, 'Error: the input file is not well formatted', './', errorfile )
                    rnacentral_ids.append( line )
    if len(rnacentral_ids) > 0:
        for rnacentral_id, exit_code in query_rnacentral( options, args, rnacentral_ids ):
            if exit_code == 0:
                print '> ' + str(rnacentral_id) + ' processed'
            else:
                print '> an error has occurred while processing ' + str(rnacentral_id) + ' has been correctly processed'
        return OK_EXIT_CODE
    else:
        print 'Error: at least one RNAcentral ID shoud be specified'
        return raiseException( ERR_EXIT_CODE, 'Error: at least one RNAcentral ID shoud be specified', './', errorfile )

def __main__():
    # Parse the command line options
    # create a fasta file and a metadata file for each of the input rnacentral ids
    usage = 'Usage: \n\t1. rnacentral.py --file file_path --fastadir fasta_dir_path --metadir metadata_dir_path\n\t2. rnacentral.py --id rnacentral_id --fastadir fasta_dir_path --metadir metadata_dir_path'
    parser = optparse.OptionParser(usage = usage)
    parser.add_option('-v', '--version', action='store_true', dest='version',
                    default=False, help='display version and exit')
    parser.add_option('-u', '--usage', action='store_true', dest='usage',
                    default=False, help='display usage')
    parser.add_option('-f', '--file', type='string',
                    action='store', dest='file', help='list of RNAcentral IDs, one for each row')
    parser.add_option('-i', '--id', type='string',
                    action='store', dest='id', help='RNAcentral id')
    parser.add_option('-o', '--fastadir', type='string', default='./',
                    action='store', dest='fastadir', help='output directory (collection) path for fasta files')
    parser.add_option('-m', '--metadir', type='string', default='./',
                    action='store', dest='metadir', help='output directory (collection) path for metadata files')
    parser.add_option('-r', '--errorfile', type='string', default='error_txt',
                    action='store', dest='errorfile', help='error file name containing error messages')

    (options, args) = parser.parse_args()
    if options.version:
        print 'Tool: ' + __version__ + '\n' + 'API: ' + __rnacentral_api_version__
    elif options.usage:
        print usage
    else:
        if options.file and options.id:
            print '--file and --id parameters can\'t be used at the same time'
        elif not options.file and not options.id:
            print 'specify at least one parameter between --file and --id'
        else:
            fasta_dir_path = options.fastadir
            # if fasta_dir_path does not exist -> create directory
            if not os.path.exists(fasta_dir_path):
                os.makedirs(fasta_dir_path)
            metadata_dir_path = options.metadir
            # if fasta_dir_path does not exist -> create directory
            if not os.path.exists(metadata_dir_path):
                os.makedirs(metadata_dir_path)
            return retrieve_data( options, args )

if __name__ == "__main__": __main__()
